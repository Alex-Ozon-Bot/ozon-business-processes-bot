import sqlite3
import os
import re
from typing import List, Tuple, Any, Optional
from datetime import datetime

class Database:
    def __init__(self, db_file: str = 'data/processes.db'):
        self.db_file = db_file
        os.makedirs(os.path.dirname(db_file), exist_ok=True)
        self.create_tables()
    
    def create_tables(self):
        """Создает необходимые таблицы в базе данных"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS processes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                process_id TEXT UNIQUE NOT NULL,
                process_name TEXT NOT NULL,
                description TEXT,
                keywords TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS suggestions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                user_name TEXT NOT NULL,
                username TEXT,
                suggestion_text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _normalize_text(self, text: str) -> str:
        """Нормализует текст: заменяет ё на е и приводит к нижнему регистру"""
        if not text:
            return ""
        return text.lower().replace('ё', 'е')
    
    def _get_word_stems(self, word: str) -> List[str]:
        """Возвращает возможные основы слова для поиска с учетом нормализации е/ё"""
        word = self._normalize_text(word.strip())
        
        if len(word) < 3:
            return [word]
        
        stems = [word]
        
        # Основные правила для русского языка - улучшенная версия
        if len(word) > 4:
            # Убираем распространенные окончания прилагательных и существительных
            if (word.endswith('ой') or word.endswith('ый') or word.endswith('ий') or 
                word.endswith('ая') or word.endswith('яя') or 
                word.endswith('ое') or word.endswith('ее') or 
                word.endswith('ые') or word.endswith('ие')):
                stems.append(word[:-2])
            
            # Окончания существительных
            elif (word.endswith('ах') or word.endswith('ях') or 
                  word.endswith('ам') or word.endswith('ям') or
                  word.endswith('ами') or word.endswith('ями') or
                  word.endswith('ов') or word.endswith('ев') or
                  word.endswith('ом') or word.endswith('ем') or
                  word.endswith('ой') or word.endswith('ей')):
                stems.append(word[:-2])
                if len(word) > 5:
                    stems.append(word[:-3])  # Для более длинных слов
                    
            elif (word.endswith('у') or word.endswith('ю') or
                  word.endswith('а') or word.endswith('я') or
                  word.endswith('о') or word.endswith('е') or
                  word.endswith('ь')):
                stems.append(word[:-1])
        
        # Специальные случаи для часто используемых слов
        special_cases = {
            'расхождение': ['расхожд', 'расхожден'],
            'расхождения': ['расхожд', 'расхожден'],
            'повреждение': ['поврежден', 'поврежд'],
            'повреждения': ['поврежден', 'поврежд'],
            'зафиксировать': ['зафиксир', 'фиксир'],
            'значительный': ['значительн', 'значим'],
            'значительные': ['значительн', 'значим'],
            'недовоз': ['недовоз', 'недов'],
            'прием': ['прием', 'приём', 'принима'],
            'приём': ['прием', 'приём', 'принима'],
            'пустой': ['пуст', 'пусто'],
            'пустая': ['пуст', 'пусто'],
            'пустые': ['пуст', 'пусто'],
            'упаковка': ['упаковк', 'упаков'],
            'упаковки': ['упаковк', 'упаков'],
            'упаковку': ['упаковк', 'упаков'],
            'селлер': ['селлер', 'селер'],
            'перевозка': ['перевоз', 'перевозк'],
            'перевозки': ['перевоз', 'перевозк'],
            'размещение': ['размещен', 'размещ'],
            'проверка': ['провер', 'проверк'],
            'целостности': ['целост', 'целостн'],
            'товара': ['товар'],
            'товары': ['товар'],
        }
        
        if word in special_cases:
            stems.extend(special_cases[word])
        
        # Добавляем варианты с ё/е для текущего слова
        if 'е' in word:
            stems.append(word.replace('е', 'ё'))
        if 'ё' in word:
            stems.append(word.replace('ё', 'е'))
        
        # Для прилагательных мужского/женского/среднего рода
        if word.endswith('ой') or word.endswith('ый') or word.endswith('ий'):
            stems.append(word[:-2] + 'ая')  # женский род
            stems.append(word[:-2] + 'ое')  # средний род
            stems.append(word[:-2] + 'ые')  # множественное число
        
        # Для существительных единственного/множественного числа
        if word.endswith('ая'):
            stems.append(word[:-2] + 'ой')  # мужской род
            stems.append(word[:-2] + 'ое')  # средний род
        
        return list(set([stem for stem in stems if len(stem) >= 3]))  # Убираем дубликаты и короткие stems

    def _calculate_relevance(self, process_data: Tuple, query_stems: List[str], original_query: str) -> int:
        """Вычисляет релевантность процесса для запроса с улучшенной логикой"""
        process_id, process_name, description, keywords = process_data
        
        # Нормализуем все текстовые поля процесса
        norm_process_name = self._normalize_text(process_name)
        norm_description = self._normalize_text(description or '')
        norm_keywords = self._normalize_text(keywords or '')
        
        # Объединяем все поля для поиска
        all_text = f"{norm_process_name} {norm_description} {norm_keywords}"
        
        relevance = 0
        
        # 1. Проверяем наличие всех стемм запроса
        found_stems = 0
        for stem in query_stems:
            if stem in all_text:
                found_stems += 1
        
        # Если не найдены все стеммы, сильно понижаем релевантность
        if found_stems < len(query_stems):
            relevance -= 20
        
        # 2. Бонус за точное совпадение фразы
        norm_query = self._normalize_text(original_query)
        if norm_query in all_text:
            relevance += 50
        
        # 3. Бонус за совпадение в названии процесса
        for stem in query_stems:
            if stem in norm_process_name:
                relevance += 10
        
        # 4. Бонус за совпадение в ключевых словах
        for stem in query_stems:
            if stem in norm_keywords:
                relevance += 8
        
        # 5. Бонус за совпадение в описании
        for stem in query_stems:
            if stem in norm_description:
                relevance += 5
        
        # 6. Бонус за нахождение всех слов запроса близко друг к другу
        words_in_text = 0
        for stem in query_stems:
            if stem in all_text:
                words_in_text += 1
        
        if words_in_text == len(query_stems):
            relevance += 15
        
        # 7. Особый бонус за процессы, которые точно соответствуют теме запроса
        # Для запроса "прием пустой упаковки" даем бонус процессам B1.6 и B1.6.2
        if "пуст" in norm_query and "упаков" in norm_query:
            if process_id in ["B1.6", "B1.6.2"]:
                relevance += 30
        
        # 8. Штраф за процессы, которые не относятся к теме
        # Например, процессы выдачи заказов не должны появляться при поиске "прием перевозки"
        if "прием" in norm_query or "приём" in norm_query:
            if process_id.startswith("B3"):  # Процессы выдачи заказов
                relevance -= 25
            if process_id.startswith("B1"):  # Процессы приема перевозок
                relevance += 20
        
        if "выдача" in norm_query:
            if process_id.startswith("B1"):  # Процессы приема перевозок
                relevance -= 25
            if process_id.startswith("B3"):  # Процессы выдачи заказов
                relevance += 20
        
        return relevance

    def search_processes(self, query: str) -> List[Tuple]:
        """Улучшенный поиск процессов с точной релевантностью"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # Разбиваем запрос на слова
        words = [word.strip() for word in query.split() if word.strip()]
        
        if not words:
            return []
        
        # Получаем все процессы для поиска
        cursor.execute('SELECT process_id, process_name, description, keywords FROM processes')
        all_processes = cursor.fetchall()
        
        # Создаем стеммы для всех слов запроса
        all_stems = []
        for word in words:
            stems = self._get_word_stems(word)
            all_stems.extend(stems)
        
        # Убираем дубликаты стемм
        all_stems = list(set(all_stems))
        
        # Ищем процессы и вычисляем релевантность
        results_with_relevance = []
        for process_data in all_processes:
            relevance = self._calculate_relevance(process_data, all_stems, query)
            if relevance > 0:  # Показываем только процессы с положительной релевантностью
                results_with_relevance.append((process_data, relevance))
        
        # Сортируем по релевантности (по убыванию)
        results_with_relevance.sort(key=lambda x: x[1], reverse=True)
        
        # Берем только топ-5 результатов
        top_results = results_with_relevance[:5]
        
        # Фильтруем только действительно релевантные процессы (релевантность > 10)
        final_results = [process for process, relevance in top_results if relevance > 10]
        
        conn.close()
        return final_results
    
    # Остальные методы остаются без изменений
    def get_all_processes(self) -> List[Tuple]:
        """Возвращает все процессы в формате (process_id, process_name)"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('SELECT process_id, process_name FROM processes ORDER BY process_id')
        processes = cursor.fetchall()
        
        conn.close()
        return processes
    
    def get_process_by_id(self, process_id: str) -> Optional[Tuple]:
        """Находит процесс по ID"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM processes WHERE process_id = ?', (process_id,))
        process = cursor.fetchone()
        
        conn.close()
        return process
    
    def save_suggestion(self, user_id: int, user_name: str, username: str, suggestion_text: str) -> bool:
        """Сохраняет пожелание пользователя в базу данных"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO suggestions (user_id, user_name, username, suggestion_text)
                VALUES (?, ?, ?, ?)
            ''', (user_id, user_name, username, suggestion_text))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Ошибка при сохранении пожелания: {e}")
            return False
    
    def get_all_suggestions(self) -> List[Tuple]:
        """Возвращает все пожелания из базы данных"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, user_id, user_name, username, suggestion_text, created_at 
                FROM suggestions 
                ORDER BY created_at DESC
            ''')
            
            suggestions = cursor.fetchall()
            conn.close()
            return suggestions
            
        except Exception as e:
            print(f"Ошибка при получении пожеланий: {e}")
            return []
    
    def get_suggestions_count(self) -> int:
        """Возвращает количество пожеланий в базе"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM suggestions')
            count = cursor.fetchone()[0]
            
            conn.close()
            return count
            
        except Exception as e:
            print(f"Ошибка при подсчете пожеланий: {e}")
            return 0
    
    def get_recent_suggestions(self, limit: int = 10) -> List[Tuple]:
        """Возвращает последние пожелания"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, user_id, user_name, username, suggestion_text, created_at 
                FROM suggestions 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (limit,))
            
            suggestions = cursor.fetchall()
            conn.close()
            return suggestions
            
        except Exception as e:
            print(f"Ошибка при получении последних пожеланий: {e}")
            return []

# Создаем глобальный экземпляр базы данных
db = Database()