[file name]: database.py
[file content begin]
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
        """Возвращает возможные основы слова для поиска с учетом различных окончаний"""
        word = self._normalize_text(word.strip())
        
        if len(word) < 2:
            return [word]
        
        stems = [word]
        
        # Базовые формы слова (убираем распространенные окончания)
        base_forms = []
        
        # Для существительных (разные падежи и числа)
        if len(word) > 3:
            # Множественное число -> единственное
            if word.endswith('и') or word.endswith('ы') or word.endswith('я'):
                base_forms.append(word[:-1] + 'й')
                base_forms.append(word[:-1] + 'ь')
                base_forms.append(word[:-1] + 'е')
            
            # Родительный падеж и другие окончания
            endings_remove = ['ов', 'ев', 'ей', 'ам', 'ям', 'ами', 'ями', 'ах', 'ях', 
                             'ом', 'ем', 'ой', 'ей', 'у', 'ю', 'а', 'я', 'о', 'е', 'ь']
            
            for ending in endings_remove:
                if word.endswith(ending) and len(word) > len(ending) + 2:
                    base_forms.append(word[:-len(ending)])
        
        # Для прилагательных
        adj_endings = ['ый', 'ий', 'ой', 'ая', 'яя', 'ое', 'ее', 'ые', 'ие', 'ым', 'им', 
                      'ой', 'ей', 'ом', 'ем', 'ую', 'юю', 'ых', 'их']
        
        for ending in adj_endings:
            if word.endswith(ending) and len(word) > len(ending) + 2:
                base_forms.append(word[:-len(ending)])
        
        # Специальные случаи для часто используемых слов в бизнес-процессах
        special_cases = {
            'излишки': ['излиш', 'излишек', 'излишк'],
            'излишек': ['излиш', 'излишек', 'излишк'],
            'расхождение': ['расхожд', 'расхожден'],
            'расхождения': ['расхожд', 'расхожден'],
            'повреждение': ['поврежден', 'поврежд'],
            'повреждения': ['поврежден', 'поврежд'],
            'зафиксировать': ['зафиксир', 'фиксир'],
            'значительный': ['значительн', 'значим'],
            'значительные': ['значительн', 'значим'],
            'недовоз': ['недовоз', 'недов'],
            'недовоза': ['недовоз', 'недов'],
            'прием': ['прием', 'приём', 'принима'],
            'приём': ['прием', 'приём', 'принима'],
            'пустой': ['пуст', 'пусто'],
            'пустая': ['пуст', 'пусто'],
            'пустые': ['пуст', 'пусто'],
            'упаковка': ['упаковк', 'упаков'],
            'упаковки': ['упаковк', 'упаков'],
            'упаковку': ['упаковк', 'упаков'],
            'селлер': ['селлер', 'селер'],
            'селлера': ['селлер', 'селер'],
            'перевозка': ['перевоз', 'перевозк'],
            'перевозки': ['перевоз', 'перевозк'],
            'размещение': ['размещен', 'размещ'],
            'проверка': ['провер', 'проверк'],
            'целостности': ['целост', 'целостн'],
            'товара': ['товар'],
            'товары': ['товар'],
            'товаров': ['товар'],
            'засыл': ['засыл'],
            'засыла': ['засыл'],
            'дубль': ['дубл'],
            'дубли': ['дубл'],
            'оформление': ['оформлен', 'оформ'],
            'приёмка': ['приемк', 'приёмк'],
            'выдача': ['выдач'],
            'возврат': ['возврат'],
            'возвраты': ['возврат'],
            'отправка': ['отправк'],
            'отправки': ['отправк'],
            'транспорт': ['транспорт'],
            'накладная': ['накладн'],
            'ттн': ['ттн', 'транспортн'],
            'штрихкод': ['штрихкод', 'шк'],
            'штрихкода': ['штрихкод', 'шк'],
        }
        
        # Добавляем специальные случаи
        if word in special_cases:
            stems.extend(special_cases[word])
        
        # Добавляем базовые формы
        stems.extend(base_forms)
        
        # Добавляем варианты с ё/е
        if 'е' in word:
            stems.append(word.replace('е', 'ё'))
        if 'ё' in word:
            stems.append(word.replace('ё', 'е'))
        
        # Убираем дубликаты и слишком короткие стеммы
        stems = list(set([stem for stem in stems if len(stem) >= 2]))
        
        return stems

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
                relevance += 5  # Бонус за каждое найденное слово
        
        # Бонус за нахождение всех слов запроса
        if found_stems == len(query_stems):
            relevance += 20
        
        # 2. Бонус за точное совпадение фразы
        norm_query = self._normalize_text(original_query)
        if norm_query in all_text:
            relevance += 50
        
        # 3. Бонус за совпадение в названии процесса
        for stem in query_stems:
            if stem in norm_process_name:
                relevance += 15
        
        # 4. Бонус за совпадение в ключевых словах
        for stem in query_stems:
            if stem in norm_keywords:
                relevance += 10
        
        # 5. Бонус за совпадение в описании
        for stem in query_stems:
            if stem in norm_description:
                relevance += 8
        
        # 6. Особые бонусы для конкретных запросов (только те, где действительно есть слова запроса)
        if "излиш" in norm_query and "излиш" in all_text:
            if process_id in ["B1.5.2"]:
                relevance += 30
        
        if "пуст" in norm_query and "упаков" in norm_query and "пуст" in all_text and "упаков" in all_text:
            if process_id in ["B1.6", "B1.6.2"]:
                relevance += 30
        
        if "недовоз" in norm_query and "недовоз" in all_text:
            if process_id in ["B1.5.1"]:
                relevance += 30
        
        if "дубл" in norm_query and "дубл" in all_text:
            if process_id in ["B1.5.2"]:
                relevance += 30
        
        return relevance

    def search_processes(self, query: str) -> List[Tuple]:
        """Улучшенный поиск процессов с расширенной морфологией"""
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
        
        # Отладочная информация
        print(f"🔍 Поиск: '{query}' -> стеммы: {all_stems}")
        
        # Ищем процессы и вычисляем релевантность
        results_with_relevance = []
        for process_data in all_processes:
            process_id, process_name, description, keywords = process_data
            
            # Нормализуем все текстовые поля процесса
            norm_process_name = self._normalize_text(process_name)
            norm_description = self._normalize_text(description or '')
            norm_keywords = self._normalize_text(keywords or '')
            
            # Объединяем все поля для поиска
            all_text = f"{norm_process_name} {norm_description} {norm_keywords}"
            
            # Проверяем, что все слова запроса присутствуют в процессе
            all_words_present = True
            for word in words:
                word_stems = self._get_word_stems(word)
                word_found = False
                for stem in word_stems:
                    if stem in all_text:
                        word_found = True
                        break
                if not word_found:
                    all_words_present = False
                    break
            
            # Если не все слова присутствуют, пропускаем процесс
            if not all_words_present:
                continue
            
            # Вычисляем релевантность только для процессов, содержащих все слова
            relevance = self._calculate_relevance(process_data, all_stems, query)
            if relevance > 5:  # Более низкий порог для большего охвата
                results_with_relevance.append((process_data, relevance))
                print(f"   ✅ {process_data[1]} (ID: {process_data[0]}) - релевантность: {relevance}")
        
        # Сортируем по релевантности (по убыванию)
        results_with_relevance.sort(key=lambda x: x[1], reverse=True)
        
        # Берем топ-5 результатов (ограничиваем до 5)
        top_results = results_with_relevance[:5]
        
        # Более мягкий фильтр релевантности
        final_results = [process for process, relevance in top_results if relevance > 8]
        
        print(f"📊 Итоговые результаты: {len(final_results)} процессов")
        
        conn.close()
        return final_results
    
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
[file content end]