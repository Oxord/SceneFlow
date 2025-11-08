from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
import torch
from datasets import Dataset

# Выбираем модель и токенизатор
model_name = "cointegrated/rubert-tiny2"
tokenizer = AutoTokenizer.from_pretrained(model_name)

# Ваши категории. Важно: O всегда должен быть первым тегом и иметь ID=0.
# Остальные теги будут пронумерованы автоматически.
label_list = [
    "O",
    "B-ОБЪЕКТ", "I-ОБЪЕКТ",
    "B-ПОДОБЪЕКТ", "I-ПОДОБЪЕКТ",
    "B-СИНОПСИС", "I-СИНОПСИС",
    "B-ВРЕМЯ_ГОДА", "I-ВРЕМЯ_ГОДА",
    "B-ПРИМЕЧАНИЕ", "I-ПРИМЕЧАНИЕ",
    "B-ПЕРСОНАЖИ", "I-ПЕРСОНАЖИ",
    "B-МАССОВКА", "I-МАССОВКА",
    "B-ГРУППОВКА", "I-ГРУППОВКА",
    "B-ГРИМ", "I-ГРИМ",
    "B-КОСТЮМ", "I-КОСТЮМ",
    "B-РЕКВИЗИТ", "I-РЕКВИЗИТ",
    "B-ИГРОВОЙ_ТРАНСПОРТ", "I-ИГРОВОЙ_ТРАНСПОРТ",
    "B-ДЕКОРАЦИЯ", "I-ДЕКОРАЦИЯ",
    "B-ПИРОТЕХНИКА", "I-ПИРОТЕХНИКА",
    "B-КАСКАДЕР_ТРЮК", "I-КАСКАДЕР_ТРЮК",
    "B-МУЗЫКА", "I-МУЗЫКА",
    "B-СПЕЦЭФФЕКТ", "I-СПЕЦЭФФЕКТ",
    "B-СПЕЦ_ОБОРУДОВАНИЕ", "I-СПЕЦ_ОБОРУДОВАНИЕ"
]

# Словарь для маппинга тегов в числовые ID и обратно
label_to_id = {label: i for i, label in enumerate(label_list)}
id_to_label = {i: label for i, label in enumerate(label_list)}

# Ваш расширенный (но всё ещё маленький) датасет
raw_datasets = [
    {
        "tokens": ["Сцена", "1", ".", "Внутри", ".", "Заброшенный", "особняк", ".", "Лето", ".", "Иван", ",", "молодой",
                   "детектив", ",", "осматривает", "комнату", "."],
        "tags": ["B-ОБЪЕКТ", "O", "O", "O", "O", "B-ДЕКОРАЦИЯ", "I-ДЕКОРАЦИЯ", "O", "B-ВРЕМЯ_ГОДА", "O", "B-ПЕРСОНАЖИ",
                 "O", "I-ПЕРСОНАЖИ", "I-ПЕРСОНАЖИ", "O", "B-СИНОПСИС", "I-СИНОПСИС", "I-СИНОПСИС"]
    },
    {
        "tokens": ["На", "столе", "лежат", "старинные", "часы", "и", "пыльная", "книга", "."],
        "tags": ["O", "O", "O", "B-РЕКВИЗИТ", "I-РЕКВИЗИТ", "O", "B-РЕКВИЗИТ", "I-РЕКВИЗИТ", "O"]
    },
    {
        "tokens": ["Появляется", "Ольга", ",", "её", "лицо", "покрыто", "грязью", "и", "искусственной", "кровью", "."],
        "tags": ["O", "B-ПЕРСОНАЖИ", "O", "O", "O", "O", "B-ГРИМ", "O", "I-ГРИМ", "I-ГРИМ", "O"]
    },
    {
        "tokens": ["Снаружи", "слышны", "звуки", "сирены", "полицейской", "машины", "."],
        "tags": ["O", "O", "O", "B-ИГРОВОЙ_ТРАНСПОРТ", "I-ИГРОВОЙ_ТРАНСПОРТ", "I-ИГРОВОЙ_ТРАНСПОРТ", "O"]
    },
    {
        "tokens": ["Несколько", "человек", "из", "массовки", "пробегают", "мимо", "окна", "."],
        "tags": ["O", "B-МАССОВКА", "I-МАССОВКА", "I-МАССОВКА", "O", "O", "O", "O"]
    },
    {
        "tokens": ["ПРИМЕЧАНИЕ", ":", "Использовать", "холодный", "свет", "для", "нагнетания", "атмосферы", "."],
        "tags": ["B-ПРИМЕЧАНИЕ", "O", "I-ПРИМЕЧАНИЕ", "I-ПРИМЕЧАНИЕ", "I-ПРИМЕЧАНИЕ", "I-ПРИМЕЧАНИЕ", "I-ПРИМЕЧАНИЕ",
                 "I-ПРИМЕЧАНИЕ", "O"]
    },
    {
        "tokens": ["Герой", "выполняет", "сложный", "прыжок", "с", "крыши", "на", "проезжающий", "автобус", "."],
        "tags": ["O", "O", "B-КАСКАДЕР_ТРЮК", "I-КАСКАДЕР_ТРЮК", "I-КАСКАДЕР_ТРЮК", "I-КАСКАДЕР_ТРЮК",
                 "I-КАСКАДЕР_ТРЮК", "I-КАСКАДЕР_ТРЮК", "I-КАСКАДЕР_ТРЮК", "O"]
    },
    {
        "tokens": ["На", "фоне", "звучит", "мрачная", "классическая", "МУЗЫКА", "."],
        "tags": ["O", "O", "O", "B-МУЗЫКА", "I-МУЗЫКА", "I-МУЗЫКА", "O"]
    },
    {
        "tokens": ["Спецэффект", ":", "Исчезновение", "Ивана", "в", "дымовой", "завесе", "."],
        "tags": ["B-СПЕЦЭФФЕКТ", "O", "I-СПЕЦЭФФЕКТ", "I-СПЕЦЭФФЕКТ", "I-СПЕЦЭФФЕКТ", "I-СПЕЦЭФФЕКТ", "I-СПЕЦЭФФЕКТ",
                 "O"]
    },
    {
        "tokens": ["Для", "съёмки", "используется", "операторский", "кран", "и", "система", "Долли", "."],
        "tags": ["O", "O", "O", "B-СПЕЦ_ОБОРУДОВАНИЕ", "I-СПЕЦ_ОБОРУДОВАНИЕ", "O", "B-СПЕЦ_ОБОРУДОВАНИЕ",
                 "I-СПЕЦ_ОБОРУДОВАНИЕ", "O"]
    },
    {
        "tokens": ["ГРУППОВКА", ":", "Две", "девушки", "разговаривают", "у", "витрины", "магазина", "."],
        "tags": ["B-ГРУППОВКА", "O", "I-ГРУППОВКА", "I-ГРУППОВКА", "I-ГРУППОВКА", "I-ГРУППОВКА", "I-ГРУППОВКА",
                 "I-ГРУППОВКА", "O"]
    },
    {
        "tokens": ["Персонаж", "одет", "в", "старинный", "плащ", "и", "шляпу", "."],
        "tags": ["O", "O", "O", "B-КОСТЮМ", "I-КОСТЮМ", "O", "I-КОСТЮМ", "O"]
    },
    {
        "tokens": ["Небольшой", "взрыв", "генератора", "."],
        "tags": ["B-ПИРОТЕХНИКА", "I-ПИРОТЕХНИКА", "I-ПИРОТЕХНИКА", "O"]
    },
    {
        "tokens": ["Объект", ":", "Эпизод", "2", ".", "Подъезд", "многоквартирного", "дома", "."],
        "tags": ["B-ОБЪЕКТ", "O", "I-ОБЪЕКТ", "I-ОБЪЕКТ", "O", "I-ОБЪЕКТ", "I-ОБЪЕКТ", "I-ОБЪЕКТ", "O"]
    },
    {
        "tokens": ["Подъезд", "завален", "мусором", "и", "граффити", ".", "Сумерки", "."],
        "tags": ["B-ДЕКОРАЦИЯ", "I-ДЕКОРАЦИЯ", "I-ДЕКОРАЦИЯ", "I-ДЕКОРАЦИЯ", "I-ДЕКОРАЦИЯ", "O", "B-ВРЕМЯ_ГОДА", "O"]
    },
    {
        "tokens": ["На", "стене", "висит", "старый", "почтовый", "ящик", "(", "Подобъект", ")", "."],
        "tags": ["O", "O", "O", "B-РЕКВИЗИТ", "I-РЕКВИЗИТ", "I-РЕКВИЗИТ", "O", "B-ПОДОБЪЕКТ", "O", "O"]
    },
    {
        "tokens": ["Сцена", "3", ".", "Улица", ".", "Осень", ".", "Падение", "Ивана", "с", "мотоцикла", "."],
        "tags": ["B-ОБЪЕКТ", "O", "O", "O", "O", "B-ВРЕМЯ_ГОДА", "O", "B-КАСКАДЕР_ТРЮК", "I-КАСКАДЕР_ТРЮК",
                 "I-КАСКАДЕР_ТРЮК", "I-КАСКАДЕР_ТРЮК", "O"]
    },
    {
        "tokens": ["Мотоцикл", "героя", "должен", "быть", "поврежден", "."],
        "tags": ["B-ИГРОВОЙ_ТРАНСПОРТ", "I-ИГРОВОЙ_ТРАНСПОРТ", "O", "O", "O", "O"]
    },
    {
        "tokens": ["На", "заднем", "плане", "группа", "людей", "ждет", "автобус", "."],
        "tags": ["O", "O", "O", "B-ГРУППОВКА", "I-ГРУППОВКА", "I-ГРУППОВКА", "I-ГРУППОВКА", "O"]
    },
    {
        "tokens": ["Его", "КОСТЮМ", ":", "кожаная", "куртка", "и", "джинсы", "."],
        "tags": ["O", "B-КОСТЮМ", "O", "I-КОСТЮМ", "I-КОСТЮМ", "O", "I-КОСТЮМ", "O"]
    },
    {
        "tokens": ["Необходима", "машина", "дыма", "для", "спецэффекта", "тумана", "."],
        "tags": ["O", "B-СПЕЦ_ОБОРУДОВАНИЕ", "I-СПЕЦ_ОБОРУДОВАНИЕ", "O", "B-СПЕЦЭФФЕКТ", "I-СПЕЦЭФФЕКТ", "O"]
    },
    {
        "tokens": ["Съемка", "велась", "на", "камеру", "Red", "Epic", "."],
        "tags": ["O", "O", "O", "B-СПЕЦ_ОБОРУДОВАНИЕ", "I-СПЕЦ_ОБОРУДОВАНИЕ", "I-СПЕЦ_ОБОРУДОВАНИЕ", "O"]
    },
    {
        "tokens": ["Весна", ".", "На", "улице", "много", "прохожих", "."],
        "tags": ["B-ВРЕМЯ_ГОДА", "O", "O", "O", "O", "B-МАССОВКА", "O"]
    },
    {
        "tokens": ["Каскадер", "Алексей", "готовится", "к", "прыжку", "."],
        "tags": ["B-КАСКАДЕР_ТРЮК", "I-КАСКАДЕР_ТРЮК", "O", "O", "I-КАСКАДЕР_ТРЮК", "O"]
    },
    {
        "tokens": ["Грим", ":", "Искусственные", "раны", "на", "лице", "."],
        "tags": ["B-ГРИМ", "O", "I-ГРИМ", "I-ГРИМ", "I-ГРИМ", "I-ГРИМ", "O"]
    },
    {
        "tokens": ["ОБЪЕКТ", ":", "Кухня", "квартиры", "Ивана", ".", "Синопсис", ":", "Герой", "готовит", "завтрак",
                   "."],
        "tags": ["B-ОБЪЕКТ", "O", "I-ОБЪЕКТ", "I-ОБЪЕКТ", "I-ОБЪЕКТ", "O", "B-СИНОПСИС", "O", "I-СИНОПСИС",
                 "I-СИНОПСИС", "I-СИНОПСИС", "O"]
    },
    {
        "tokens": ["Реквизит", ":", "Сковорода", ",", "яйца", ",", "бекон", "."],
        "tags": ["B-РЕКВИЗИТ", "O", "I-РЕКВИЗИТ", "O", "I-РЕКВИЗИТ", "O", "I-РЕКВИЗИТ", "O"]
    },
    {
        "tokens": ["На", "заднем", "плане", "играет", "фоновая", "музыка", "джаз", "."],
        "tags": ["O", "O", "O", "O", "B-МУЗЫКА", "I-МУЗЫКА", "I-МУЗЫКА", "O"]
    },
    {
        "tokens": ["Зима", ".", "Снег", "покрывает", "декорации", "леса", "."],
        "tags": ["B-ВРЕМЯ_ГОДА", "O", "O", "O", "B-ДЕКОРАЦИЯ", "I-ДЕКОРАЦИЯ", "O"]
    }
]

# Конвертируем наш список в Hugging Face Dataset
dataset = Dataset.from_list(raw_datasets)


def tokenize_and_align_labels(examples):
    tokenized_inputs = tokenizer(examples["tokens"], truncation=True, is_split_into_words=True)
    labels = []
    for i, label in enumerate(examples["tags"]):
        word_ids = tokenized_inputs.word_ids(batch_index=i)
        previous_word_idx = None
        label_ids = []
        for word_idx in word_ids:
            # Специальные токены (CLS, SEP) или токены, не принадлежащие никакому слову, получают -100
            if word_idx is None:
                label_ids.append(-100)
            # Если это тот же токен, что и предыдущий, и он не является первым subword-токеном,
            # присваиваем -100
            elif word_idx == previous_word_idx:
                label_ids.append(-100)
            # Если это новый токен или первый subword-токен, присваиваем оригинальный тег
            else:
                label_ids.append(label_to_id[label[word_idx]])
            previous_word_idx = word_idx
        labels.append(label_ids)
    tokenized_inputs["labels"] = labels
    return tokenized_inputs


# Применяем функцию к нашему датасету
tokenized_dataset = dataset.map(tokenize_and_align_labels, batched=True)

# Разделение на train/validation (в реальном проекте у вас уже будут разделены)
# Увеличил обучающую выборку, чтобы на малом датасете хоть что-то училось
train_size = int(len(tokenized_dataset) * 0.8)
eval_size = len(tokenized_dataset) - train_size

# Убедимся, что размеры не нулевые, особенно для очень маленьких датасетов
if train_size == 0 and len(tokenized_dataset) > 0:
    train_size = 1
    eval_size = len(tokenized_dataset) - 1 if len(tokenized_dataset) > 1 else 0
elif train_size == 0 and len(tokenized_dataset) == 0:
    print("Внимание: Датасет пуст. Обучение невозможно.")
    exit()

shuffled_dataset = tokenized_dataset.shuffle(seed=42)
train_dataset = shuffled_dataset.select(range(train_size))
eval_dataset = shuffled_dataset.select(range(train_size, train_size + eval_size))

print(f"Train dataset size: {len(train_dataset)}")
print(f"Eval dataset size: {len(eval_dataset)}")

from transformers import TrainingArguments, Trainer, DataCollatorForTokenClassification, AutoModelForTokenClassification
import numpy as np
from seqeval.metrics import f1_score, precision_score, recall_score, classification_report

# Загружаем модель с учетом количества ваших лейблов
model = AutoModelForTokenClassification.from_pretrained(model_name, num_labels=len(label_list), id2label=id_to_label,
                                                        label2id=label_to_id)

# Аргументы обучения
training_args = TrainingArguments(
    output_dir="./results",
    eval_strategy="epoch",
    learning_rate=2e-5,
    per_device_train_batch_size=4,  # Уменьшил батч сайз для стабильности на малом датасете
    per_device_eval_batch_size=4,  # Уменьшил батч сайз
    num_train_epochs=10,  # Увеличил количество эпох
    weight_decay=0.01,
    logging_dir="./logs",
    logging_steps=1,  # Логировать чаще, чтобы видеть прогресс
    save_strategy="epoch",
    load_best_model_at_end=True,
    metric_for_best_model="f1",
    push_to_hub=False,
    report_to="none",
)

data_collator = DataCollatorForTokenClassification(tokenizer=tokenizer)


def compute_metrics(p):
    predictions, labels = p
    predictions = np.argmax(predictions, axis=2)
    # Удаляем токены с -100
    true_labels = [[id_to_label[l] for l in label if l != -100] for label in labels]
    true_predictions = [[id_to_label[p] for (p, l) in zip(prediction, label) if l != -100] for prediction, label in
                        zip(predictions, labels)]

    # Отфильтруем пустые списки, чтобы seqeval не выкидывал ошибку
    # Это может произойти, если в батче нет ни одного токена с реальным лейблом
    filtered_true_labels = []
    filtered_true_predictions = []
    for t_l, t_p in zip(true_labels, true_predictions):
        if t_l and t_p:  # Убедимся, что списки не пустые
            filtered_true_labels.append(t_l)
            filtered_true_predictions.append(t_p)

    if not filtered_true_labels:  # Если после фильтрации ничего не осталось
        return {"f1": 0.0, "precision": 0.0, "recall": 0.0}

    f1 = f1_score(filtered_true_labels, filtered_true_predictions, average="micro")
    precision = precision_score(filtered_true_labels, filtered_true_predictions, average="micro")
    recall = recall_score(filtered_true_labels, filtered_true_predictions, average="micro")
    return {
        "f1": f1,
        "precision": precision,
        "recall": recall,
    }


trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    tokenizer=tokenizer,
    data_collator=data_collator,
    compute_metrics=compute_metrics,
)

print("Starting training...")
trainer.train()
print("Training finished.")

# Загружаем лучшую модель, которая была сохранена тренером
# (обычно это последний чекпоинт, если load_best_model_at_end=True)
ner_pipeline = pipeline("token-classification", model=model, tokenizer=tokenizer, aggregation_strategy="simple")

print("\n--- Результаты предсказаний ---")
text = "Сцена 5. Зима. Главный герой Джон Смит сидит в старой машине. Грим: синяки под глазами. Реквизит: пистолет."
results = ner_pipeline(text)
for entity in results:
    print(f"Слово: '{entity['word']}', Категория: '{entity['entity_group']}', Вероятность: {entity['score']:.2f}")

print("\n--- Результаты предсказаний 2 ---")
text2 = "Пиротехника: небольшой взрыв. Костюм: костюм космонавта. Спец. оборудование: камера Go-Pro."
results2 = ner_pipeline(text2)
for entity in results2:
    print(f"Слово: '{entity['word']}', Категория: '{entity['entity_group']}', Вероятность: {entity['score']:.2f}")

print("\n--- Результаты предсказаний 3 ---")
text3 = "Синопсис: два каскадера выполняют сложный трюк на мотоцикле. Музыка: энергичный рок."
results3 = ner_pipeline(text3)
for entity in results3:
    print(f"Слово: '{entity['word']}', Категория: '{entity['entity_group']}', Вероятность: {entity['score']:.2f}")
