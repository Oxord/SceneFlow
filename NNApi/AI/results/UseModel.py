from transformers import pipeline

# Загружаем лучшую модель, которая была сохранена тренером
# (обычно это последний чекпоинт, если load_best_model_at_end=True)
# Если вы хотите загрузить конкретный чекпоинт, укажите его путь:
# model_path = "./results/checkpoint-XXXX" # замените XXXX на номер вашего чекпоинта
# pipeline = pipeline("token-classification", model=model_path, tokenizer=tokenizer, aggregation_strategy="simple")

# Или, если модель загружена в переменную `model` после обучения
ner_pipeline = pipeline("token-classification", model=model, tokenizer=tokenizer, aggregation_strategy="simple")

# Теперь можем использовать пайплайн для предсказаний
text = "Я хочу купить яблоки и груши в Евроопте, а также зайти в аптеку."
results = ner_pipeline(text)

print("\n--- Результаты предсказаний ---")
for entity in results:
    print(f"Слово: '{entity['word']}', Категория: '{entity['entity']}', Вероятность: {entity['score']:.2f}")

# Пример другого текста
text2 = "Молоко и кефир продаются в Перекрёстке."
results2 = ner_pipeline(text2)
print("\n--- Результаты предсказаний 2 ---")
for entity in results2:
    print(f"Слово: '{entity['word']}', Категория: '{entity['entity']}', Вероятность: {entity['score']:.2f}")