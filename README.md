# LLM-Based Agentic Python Functions Debugger

Автоматическая система исправления багов в Python коде на основе LLM-агента с использованием LangGraph.

## 🎯 Описание

Этот проект представляет собой агентную систему для автоматического обнаружения и исправления ошибок в Python коде. Агент использует локальную LLM модель (qwen2.5-coder-7b-instruct через LM Studio) для итеративного тестирования кода, анализа ошибок и предложения исправлений до тех пор, пока все тесты не будут пройдены или не достигнут лимит итераций.

### Ключевые особенности:

- **Агентный подход**: Использует LangGraph для построения графа с узлами рассуждений и выполнения инструментов
- **Итеративное исправление**: До 7 попыток на исправление одной задачи
- **Автоматическое тестирование**: Каждое исправление автоматически тестируется с предоставленными тестами
- **Безопасное выполнение**: Код выполняется в изолированной среде с таймаутом
- **Анализ ошибок**: Встроенный анализатор для понимания типов ошибок

## 📊 Метрики производительности

На датасете HumanEvalFix (50 задач):

- **Pass@1**: ~42% - процент задач, где агент нашёл правильное решение (независимо от количества попыток)
- **First Submission Accuracy**: ~30-40% - процент задач, где первый сабмит был корректным
- **Максимум итераций**: 7 попыток на задачу

## 🏗️ Архитектура

### Компоненты системы:

1. **Agent Node** (`agent/agent.py`)
   - Основной узел рассуждений агента
   - Анализирует код и планирует исправления
   - Взаимодействует с LLM для генерации решений
   - Использует специальные маркеры `<<<FIXED_CODE_START>>>` и `<<<FIXED_CODE_END>>>` для выделения исправленного кода

2. **Tools Node** (`agent/agent.py`)
   - Выполняет вызовы инструментов (тестирование, анализ ошибок)
   - Автоматически тестирует каждый новый вариант исправленного кода
   - Собирает результаты выполнения и статистику
   - Формирует обратную связь для агента

3. **State** (`agent/state.py`)
   - Расширенное состояние на базе `MessagesState` из LangGraph
   - Хранит историю сообщений, попыток исправления и результатов тестирования
   - Отслеживает количество итераций и статус решения задачи

4. **Tools** (инструменты):
   - **python_code_executor** (`tools/python_code_executor.py`) - безопасное выполнение Python кода в изолированной среде с таймаутом 10 секунд
   - **error_analyzer** (`tools/error_analyzer.py`) - анализ типов ошибок и предложение потенциальных решений

### Граф работы агента:

```
START → agent_node → should_continue → tools_node → agent_node → ... → END
                          ↓
                         end
```

**Логика переходов:**
- `should_continue()` проверяет:
  - Достигнут ли лимит итераций
  - Исправлен ли код (`is_fixed == True`)
  - Есть ли непроверенный кандидат на исправление
  - Есть ли вызовы инструментов от LLM
- Если задача решена или достигнут лимит → переход на `END`
- Если есть работа для инструментов → переход на `tools_node`
- Иначе → переход на `END`

## 🚀 Установка

### Предварительные требования:

- Python 3.9+
- LM Studio (для локального запуска LLM)
- Модель qwen2.5-coder:7b-instruct в LM Studio

### Шаги установки:

```bash
# 1. Клонируйте репозиторий
git clone https://github.com/yourusername/llm-based-agentic-python-functions-debugger.git
cd llm-based-agentic-python-functions-debugger

# 2. Создайте виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/macOS
# или
venv\Scripts\activate  # Windows

# 3. Установите зависимости
pip install -r requirements.txt

# 4. Для работы прогресс-баров в Jupyter Notebook/Lab
pip install ipywidgets jupyterlab-widgets

# 5. Настройте переменные окружения
cp .env.example .env
# Отредактируйте .env файл и укажите параметры подключения к LM Studio
```

### Настройка LM Studio:

1. Скачайте и установите [LM Studio](https://lmstudio.ai/)
2. Загрузите модель `qwen2.5-coder:7b-instruct`
3. Запустите локальный сервер (обычно на `http://localhost:1234`)
4. Убедитесь, что модель поддерживает function calling

## 📝 Конфигурация

Создайте файл `.env` в корне проекта:

```env
# LLM Configuration
OPENAI_API_BASE=http://localhost:1234/v1
OPENAI_API_KEY=lm-studio  # Любое значение для LM Studio
MODEL_NAME=qwen2.5-coder-7b-instruct

# Agent Configuration
MAX_ITERATIONS=7
TIMEOUT_SECONDS=10
```

## 💻 Использование

### Базовое использование через Python:

```python
from graph import create_debug_agent_graph
from agent.state import DebugAgentState
from langchain_core.messages import HumanMessage

# Создайте граф агента
graph = create_debug_agent_graph()

# Подготовьте данные
buggy_code = """
def has_close_elements(numbers, threshold):
    for idx, elem in enumerate(numbers):
        for idx2, elem2 in enumerate(numbers):
            if idx != idx2:
                distance = elem - elem2  # BUG: должно быть abs(elem - elem2)
                if distance < threshold:
                    return True
    return False
"""

test_code = """
def check(has_close_elements):
    assert has_close_elements([1.0, 2.0, 3.9, 4.0, 5.0, 2.2], 0.3) == True
    assert has_close_elements([1.0, 2.0, 3.9, 4.0, 5.0, 2.2], 0.05) == False
    
check(has_close_elements)
"""

# Запустите исправление
user_message = f"Fix the following Python code:\n{buggy_code} and for testing use this code: \n{test_code}"

initial_state = {
    "messages": [HumanMessage(content=user_message)],
    "original_buggy_code": buggy_code,
    "test_code": test_code,
    "max_iterations": 7,
    "iterations": 0,
    "is_fixed": False,
    "fixed_code": "",
    "submit_idx": -1,
    "submissions": [],
    "first_pass": None
}

final_state = graph.invoke(initial_state)

print(f"✅ Код исправлен: {final_state['is_fixed']}")
print(f"📊 Использовано итераций: {final_state['iterations']}")
print(f"📝 Исправленный код:\n{final_state['fixed_code']}")
```

### Использование через Jupyter Notebook:

Откройте `evaluation/humanevalfix_eval.ipynb` и выполните ячейки для:

1. Загрузки датасета HumanEvalFix
2. Запуска агента на множестве задач
3. Подсчёта метрик качества

```python
from datasets import load_dataset
from tqdm.notebook import tqdm

# Загрузите датасет
dataset = load_dataset("bigcode/humanevalpack", "python")
problems = list(dataset["test"])[:50]  # первые 50 задач

# Запустите оценку
results = []
for problem in tqdm(problems):
    result = fix_code(
        buggy_code=problem["buggy_solution"],
        test_code=problem["test"],
        max_iterations=7
    )
    results.append(result)

# Посчитайте метрики
from metrics.pass_at_k import estimate_pass_at_1, estimate_first_submission_accuracy

pass_at_1 = estimate_pass_at_1(results)
first_pass_acc = estimate_first_submission_accuracy(results)

print(f"Pass@1: {pass_at_1:.2%}")
print(f"First Pass Accuracy: {first_pass_acc:.2%}")
```

## 📁 Структура проекта

```
llm-based-agentic-python-functions-debugger/
├── agent/                          # Основная логика агента
│   ├── __init__.py
│   ├── agent.py                   # Узлы графа (agent_node, tools_node, should_continue)
│   └── state.py                   # Определение состояния DebugAgentState
│
├── tools/                          # Инструменты агента
│   ├── __init__.py
│   ├── python_code_executor.py    # Выполнение Python кода в песочнице
│   └── error_analyzer.py          # Анализ типов ошибок
│
├── llm/                            # Конфигурация LLM
│   ├── __init__.py
│   └── qwen2_5_coder_7b_instruct.py  # Инициализация LLM клиента
│
├── metrics/                        # Метрики оценки
│   ├── __init__.py
│   └── pass_at_k.py               # Pass@1 и First Submission Accuracy
│
├── evaluation/                     # Оценка на датасетах
│   ├── __init__.py
│   ├── basic_test.ipynb           # Базовые тесты
│   └── humanevalfix_eval.ipynb    # Оценка на HumanEvalFix
│
├── graph.py                        # Создание LangGraph графа
├── requirements.txt                # Зависимости проекта
├── .env.example                    # Пример конфигурации
└── README.md                       # Этот файл
```

## 🔧 Основные функции и API

### `create_debug_agent_graph()`

Создаёт и компилирует граф агента для исправления кода.

**Возвращает:**
- Скомпилированный граф LangGraph

**Пример:**
```python
from graph import create_debug_agent_graph
graph = create_debug_agent_graph()
```

### `fix_code(buggy_code, test_code="", max_iterations=7)`

Высокоуровневая функция для исправления кода (определена в `evaluation/humanevalfix_eval.ipynb`).

**Параметры:**
- `buggy_code` (str): Код с ошибками, который нужно исправить
- `test_code` (str): Тестовый код для проверки корректности исправления
- `max_iterations` (int): Максимальное количество попыток исправления

**Возвращает словарь:**
```python
{
    "fixed_code": str,           # Исправленный код (последняя версия)
    "is_fixed": bool,            # True если все тесты прошли успешно
    "iterations": int,           # Количество использованных итераций
    "messages": List[Message],   # История всех сообщений в диалоге
    "submissions": List[Dict],   # История всех попыток с результатами
    "first_pass": bool           # True если первая попытка была успешной
}
```

**Структура элемента submissions:**
```python
{
    "idx": int,          # Порядковый номер попытки
    "code": str,         # Код, который был протестирован
    "passed": bool,      # Прошли ли тесты
    "stderr": str        # Stderr из выполнения (если были ошибки)
}
```

### `python_code_executor(code: str, test_code: str = "")`

Инструмент для безопасного выполнения Python кода.

**Параметры:**
- `code` (str): Код для выполнения
- `test_code` (str, optional): Дополнительный тестовый код

**Возвращает:** Строку с результатом выполнения в формате:
```
STDOUT:
<вывод программы>

STDERR:
<ошибки, если есть>

EXIT_CODE: <код возврата>
```

### `error_analyzer(error_message: str, code: str)`

Инструмент для анализа ошибок.

**Параметры:**
- `error_message` (str): Сообщение об ошибке
- `code` (str): Код, вызвавший ошибку

**Возвращает:** Строку с анализом и рекомендациями по исправлению

## 📈 Метрики

### Pass@1

**Определение:** Процент задач, для которых агент нашёл корректное решение (независимо от количества попыток).

**Формула:**
```
Pass@1 = (количество решённых задач) / (общее количество задач)
```

Задача считается решённой, если `is_fixed == True` в финальном состоянии.

### First Submission Accuracy

**Определение:** Процент задач, где **первая** отправленная версия кода прошла все тесты.

**Формула:**
```
First Submission Accuracy = (количество задач с first_pass=True) / (общее количество задач)
```

Это более строгая метрика, показывающая качество первого решения агента без итераций.

## 🎓 Принцип работы

### Основной цикл работы:

1. **Инициализация**: Пользователь предоставляет багованный код и тесты
2. **Agent Node**: 
   - LLM анализирует код
   - Может вызвать инструменты для тестирования или анализа
   - Генерирует исправленную версию кода
3. **Should Continue**: Проверяет условия продолжения работы
4. **Tools Node**:
   - Выполняет вызванные инструменты
   - Автоматически тестирует новый код с тестами
   - Формирует фидбек для агента
5. **Повтор**: Процесс повторяется до успеха или достижения лимита итераций

### Маркеры для кода:

Агент использует специальные маркеры для выделения исправленного кода:

```python
<<<FIXED_CODE_START>>>
def corrected_function():
    # исправленный код здесь
    pass
<<<FIXED_CODE_END>>>
```

Система автоматически извлекает код между маркерами и отправляет на тестирование.

## 🐛 Известные проблемы и ограничения

### 1. **Function Calling не всегда работает**
- Локальные модели (особенно 7B параметров) хуже справляются с вызовом инструментов
- LLM может игнорировать доступные инструменты и пытаться решить задачу без тестирования
- **Решение**: Используйте более мощные модели (GPT-4, Claude 3.5) или добавьте принудительный первый вызов

### 2. **Ограничение в 7 итераций**
- Сложные баги могут требовать больше попыток
- **Решение**: Увеличьте `max_iterations` в конфигурации

### 3. **Производительность модели 7B**
- Модель qwen2.5-coder-7b меньше и слабее, чем GPT-4
- Может не справляться со сложными логическими ошибками
- **Решение**: Используйте более мощные модели через API

### 4. **Таймаут выполнения**
- Код с бесконечными циклами прерывается через 10 секунд
- Может быть недостаточно для некоторых задач
- **Решение**: Увеличьте таймаут в `python_code_executor.py`

### 5. **Отсутствие кэширования**
- Одинаковый код тестируется повторно
- **Будущее улучшение**: Добавить кэш результатов тестирования

## 🚀 Планы развития

- [ ] **Поддержка других LLM**: GPT-4, Claude 3.5, DeepSeek Coder
- [ ] **Few-shot примеры**: Добавить примеры исправлений в промт
- [ ] **Улучшение промтов**: Оптимизация системных сообщений
- [ ] **Кэширование результатов**: Избегать повторного тестирования
- [ ] **Расширенная аналитика**: Анализ типов ошибок и паттернов исправлений
- [ ] **Web-интерфейс**: Удобный UI для работы с агентом
- [ ] **Поддержка других языков**: JavaScript, TypeScript, Java
- [ ] **Увеличение контекста**: Работа с большими файлами
- [ ] **Метрика Pass@k**: Поддержка оценки с k попытками

## 📚 Зависимости

Основные библиотеки:

- **langgraph** (>=0.2.0) - граф-фреймворк для построения агентов
- **langchain** (>=0.3.0) - фреймворк для работы с LLM
- **langchain-openai** (>=0.2.0) - интеграция с OpenAI-совместимыми API
- **datasets** (>=2.14.0) - загрузка датасетов HuggingFace
- **python-dotenv** (>=1.0.0) - управление переменными окружения
- **ipywidgets** - интерактивные виджеты для Jupyter
- **tqdm** - прогресс-бары

## 🔬 Оценка качества

Для воспроизведения результатов:

```bash
# 1. Запустите LM Studio с моделью qwen2.5-coder:7b-instruct
# 2. Откройте Jupyter Lab
jupyter lab

# 3. Откройте evaluation/humanevalfix_eval.ipynb
# 4. Выполните все ячейки
```

Результаты будут включать:
- Pass@1 метрику
- First Submission Accuracy
- Детальный анализ каждой задачи
- Историю сообщений и попыток исправления

## 📄 Лицензия

MIT License

## 👥 Автор

Roman Avanesov

## 🙏 Благодарности

- [LangChain](https://github.com/langchain-ai/langchain) - мощный фреймворк для работы с LLM
- [LangGraph](https://github.com/langchain-ai/langgraph) - граф-фреймворк для построения агентных систем
- [HumanEvalPack](https://huggingface.co/datasets/bigcode/humanevalpack) - датасет для оценки качества исправления кода
- [LM Studio](https://lmstudio.ai/) - удобный инструмент для запуска локальных LLM
- [Qwen Team](https://github.com/QwenLM) - за отличную модель для работы с кодом

---

**⭐ Если проект был полезен, поставьте звезду на GitHub!**

