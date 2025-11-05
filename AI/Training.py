from transformers import TrainingArguments, Trainer, DataCollatorForTokenClassification, AutoModelForTokenClassification
import numpy as np
from seqeval.metrics import f1_score, precision_score, recall_score, classification_report

# Загружаем модель с учетом количества ваших лейблов
model = AutoModelForTokenClassification.from_pretrained(model_name, num_labels=len(label_list), id2label=id_to_label,
                                                        label2id=label_to_id)

# Аргументы обучения
training_args = TrainingArguments(
    output_dir="./results",  # Каталог для сохранения результатов
    evaluation_strategy="epoch",  # Оценивать модель после каждой эпохи
    learning_rate=2e-5,  # Скорость обучения
    per_device_train_batch_size=16,  # Размер батча для обучения
    per_device_eval_batch_size=16,  # Размер батча для оценки
    num_train_epochs=5,  # Количество эпох обучения
    weight_decay=0.01,  # Регуляризация
    logging_dir="./logs",  # Каталог для логов TensorBoard
    logging_steps=10,
    save_strategy="epoch",  # Сохранять модель после каждой эпохи
    load_best_model_at_end=True,  # Загрузить лучшую модель по итогам обучения
    metric_for_best_model="f1",  # Метрика для выбора лучшей модели
    push_to_hub=False,  # Не загружать на Hugging Face Hub
    report_to="none",  # Отключить интеграцию с другими платформами для отчетов
)

# Data Collator отвечает за батчинг и паддинг (дополнение до одинаковой длины) токенизированных последовательностей.
data_collator = DataCollatorForTokenClassification(tokenizer=tokenizer)


# Функция для вычисления метрик
def compute_metrics(p):
    predictions, labels = p
    predictions = np.argmax(predictions, axis=2)

    # Удаляем токены с -100
    true_labels = [[id_to_label[l] for l in label if l != -100] for label in labels]
    true_predictions = [[id_to_label[p] for (p, l) in zip(prediction, label) if l != -100] for prediction, label in
                        zip(predictions, labels)]

    # Используем seqeval для расчета метрик NER
    # F1-score - это среднее гармоническое точности и полноты. Важная метрика для NER.
    f1 = f1_score(true_labels, true_predictions, average="micro")
    precision = precision_score(true_labels, true_predictions, average="micro")
    recall = recall_score(true_labels, true_predictions, average="micro")

    # Можно также вывести полный отчет
    # print(classification_report(true_labels, true_predictions))

    return {
        "f1": f1,
        "precision": precision,
        "recall": recall,
    }


# Создаем Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    tokenizer=tokenizer,
    data_collator=data_collator,
    compute_metrics=compute_metrics,
)

# Запускаем обучение
print("Starting training...")
trainer.train()
print("Training finished.")

# Оценим модель на тестовой выборке (если есть)
# results = trainer.evaluate(eval_dataset)
# print(results)