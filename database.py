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
        
        # Улучшенная обработка множественного числа
        plural_endings = [
            # Множественное число существительных
            ('ов', ''), ('ев', ''), ('ей', ''), ('ий', 'ий'), ('ые', 'ый'), ('ие', 'ий'),
            ('ам', ''), ('ям', ''), ('ами', ''), ('ями', ''), ('ах', ''), ('ях', ''),
            # Родительный падеж и другие окончания
            ('ом', ''), ('ем', ''), ('ой', ''), ('ей', ''), ('у', ''), ('ю', ''),
            ('а', ''), ('я', ''), ('о', ''), ('е', ''), ('ь', ''), ('ы', ''), ('и', '')
        ]
        
        # Специальные преобразования множественного числа
        plural_transforms = {
            'засылы': 'засыл',
            'засылов': 'засыл',
            'излишки': 'излиш',
            'излишков': 'излиш',
            'дубли': 'дубл',
            'дублей': 'дубл',
            'повреждения': 'поврежд',
            'расхождения': 'расхожд',
            'недовозы': 'недовоз',
            'отправки': 'отправк',
            'перевозки': 'перевоз',
            'товары': 'товар',
            'товаров': 'товар',
            'упаковки': 'упаковк',
            'наклейки': 'наклейк',
            'накладные': 'накладн',
            'возвраты': 'возврат',
            'селлера': 'селлер',
            'селлеры': 'селлер',
            'коробки': 'коробк',
            'ящики': 'ящик',
            'ячейки': 'ячейк',
            'процессы': 'процесс',
            'процессов': 'процесс',
            'заказы': 'заказ',
            'заказов': 'заказ',
            'клиенты': 'клиент',
            'клиентов': 'клиент',
            'водители': 'водитель',
            'водителей': 'водитель',
            'перевозки': 'перевозк',
            'перевозок': 'перевозк',
            'отправления': 'отправлен',
            'отправлений': 'отправлен'
        }
        
        # Проверяем специальные преобразования
        if word in plural_transforms:
            stems.append(plural_transforms[word])
        
        # Применяем правила окончаний
        for ending, replacement in plural_endings:
            if word.endswith(ending) and len(word) > len(ending) + 1:
                base = word[:-len(ending)] + replacement
                if len(base) >= 2:  # Проверяем, что основа не слишком короткая
                    base_forms.append(base)
        
        # Для существительных мужского рода с окончанием на согласную
        if len(word) > 2 and word[-1] not in 'аеёиоуыэюя':
            # Добавляем возможные формы с разными окончаниями
            possible_endings = ['а', 'у', 'ом', 'е', 'ы', 'ов', 'ам', 'ами', 'ах']
            for ending in possible_endings:
                if word + ending in plural_transforms.values():
                    stems.append(word + ending)
        
        # Для существительных женского рода с окончанием на а/я
        if word.endswith(('а', 'я')) and len(word) > 2:
            base = word[:-1]
            stems.extend([base + 'а', base + 'у', base + 'ой', base + 'е', base + 'ы', base + '', base + 'ам', base + 'ами', base + 'ах'])
        
        # Добавляем специальные случаи
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
            'недовозы': ['недовоз', 'недов'],
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
            'селлеры': ['селлер', 'селер'],
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
            'засылы': ['засыл'],
            'дубль': ['дубл'],
            'дубли': ['дубл'],
            'оформление': ['оформлен', 'оформ'],
            'оформить': ['оформ', 'оформлен'],
            'приёмка': ['приемк', 'приёмк'],
            'выдача': ['выдач', 'выда'],
            'выдать': ['выдач', 'выда'],
            'выдают': ['выдач', 'выда'],
            'выдаче': ['выдач', 'выда'],
            'выдач': ['выдач', 'выда'],
            'экземпляр': ['экземпляр'],
            'экземпляров': ['экземпляр'],
            'экземпляры': ['экземпляр'],
            'экземпляра': ['экземпляр'],
            'возврат': ['возврат'],
            'возвраты': ['возврат'],
            'отправка': ['отправк'],
            'отправки': ['отправк'],
            'транспорт': ['транспорт'],
            'накладная': ['накладн'],
            'накладные': ['накладн'],
            'ттн': ['ттн', 'транспортн'],
            'штрихкод': ['штрихкод', 'шк'],
            'штрихкода': ['штрихкод', 'шк'],
            'штрихкоды': ['штрихкод', 'шк'],
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

    def _calculate_relevance(self, process_data: Tuple, query_stems: List[str], original_query: str, found_words_count: int, total_words: int) -> int:
        """Вычисляет релевантность процесса для запроса с улучшенной логикой"""
        process_id, process_name, description, keywords = process_data
        
        # Нормализуем все текстовые поля процесса
        norm_process_name = self._normalize_text(process_name)
        norm_description = self._normalize_text(description or '')
        norm_keywords = self._normalize_text(keywords or '')
        
        # Объединяем все поля для поиска
        all_text = f"{norm_process_name} {norm_description} {norm_keywords}"
        
        relevance = 0
        
        # 1. Самый важный критерий - количество найденных слов (максимальный бонус)
        if found_words_count == total_words:
            # Все слова найдены - максимальный бонус
            relevance += 100
        elif found_words_count == total_words - 1:
            # Найдены все слова кроме одного - высокий бонус
            relevance += 70
        elif found_words_count >= total_words - 2:
            # Найдено большинство слов - средний бонус
            relevance += 40
        else:
            # Найдено мало слов - минимальный бонус
            relevance += found_words_count * 10
        
        # 2. Проверяем наличие всех стемм запроса
        found_stems = 0
        for stem in query_stems:
            if stem in all_text:
                found_stems += 1
                relevance += 3  # Небольшой бонус за каждое найденное слово
        
        # 3. Бонус за точное совпадение фразы
        norm_query = self._normalize_text(original_query)
        if norm_query in all_text:
            relevance += 50
        
        # 4. Бонус за совпадение в названии процесса
        for stem in query_stems:
            if stem in norm_process_name:
                relevance += 15
        
        # 5. Бонус за совпадение в ключевых словах
        for stem in query_stems:
            if stem in norm_keywords:
                relevance += 10
        
        # 6. Бонус за совпадение в описании
        for stem in query_stems:
            if stem in norm_description:
                relevance += 8
        
        # 7. Особые бонусы для конкретных запросов (только те, где действительно есть слова запроса)
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
        
        if "засыл" in norm_query and "засыл" in all_text:
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
        print(f"🔍 Поиск: '{query}' -> слова: {words}, стеммы: {all_stems}")
        
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
            
            # Считаем количество найденных слов (улучшенная логика)
            found_words_count = 0
            for word in words:
                word_stems = self._get_word_stems(word)
                word_found = False
                
                # Проверяем все стеммы слова
                for stem in word_stems:
                    if stem in all_text:
                        word_found = True
                        break
                
                # Также проверяем оригинальное слово
                if not word_found and self._normalize_text(word) in all_text:
                    word_found = True
                    
                if word_found:
                    found_words_count += 1
            
            # Если не найдено ни одного слова, пропускаем процесс
            if found_words_count == 0:
                continue
            
            # Вычисляем релевантность с учетом количества найденных слов
            relevance = self._calculate_relevance(process_data, all_stems, query, found_words_count, len(words))
            
            results_with_relevance.append((process_data, relevance, found_words_count))
            print(f"   ✅ {process_data[1]} (ID: {process_data[0]}) - найдено слов: {found_words_count}/{len(words)}, релевантность: {relevance}")
        
        # Если есть результаты, находим максимальное количество найденных слов
        if results_with_relevance:
            max_found_words = max(found_words for _, _, found_words in results_with_relevance)
            print(f"📊 Максимальное количество найденных слов: {max_found_words}/{len(words)}")
            
            # Оставляем только процессы с максимальным количество найденных слов
            filtered_results = [(process, relevance) for process, relevance, found_words in results_with_relevance 
                              if found_words == max_found_words]
            
            # Сортируем по релевантности (по убыванию)
            filtered_results.sort(key=lambda x: x[1], reverse=True)
            
            # Берем топ-5 результатов
            final_results = [process for process, relevance in filtered_results[:5]]
            
            print(f"📊 Итоговые результаты: {len(final_results)} процессов (с {max_found_words}/{len(words)} словами)")
        else:
            final_results = []
            print(f"📊 Итоговые результаты: 0 процессов")
        
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