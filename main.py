import pandas as pd
import numpy as np

# Загрузка данных из Excel файла
file_path = 'path_to_your_file.xlsx'  # Укажите путь к вашему Excel файлу
data = pd.read_excel(file_path)

# Предполагается, что у вас есть колонки 'product', 'sales', 'stock', 'date'
data['date'] = pd.to_datetime(data['date'])

# Убираем субботы и воскресенья
data['day_of_week'] = data['date'].dt.dayofweek
data = data[data['day_of_week'] < 5]  # 0 - понедельник, 1 - вторник, ..., 4 - пятница

# Группируем данные по продуктам и месяцам, чтобы вычислить средние продажи по месяцам
data['month'] = data['date'].dt.to_period('M')
monthly_sales = data.groupby(['product', 'month'])['sales'].sum().reset_index()

# Вычисляем коэффициент сезонности для каждого продукта
seasonal_factors = monthly_sales.groupby('product')['sales'].apply(lambda x: x / x.mean()).reset_index()
seasonal_factors.columns = ['product', 'seasonal_factor']

# Объединяем с исходными данными
data = data.merge(seasonal_factors, on='product', how='left')

# Вычисляем средние продажи за день
data['avg_daily_sales'] = data.groupby(['product', 'month'])['sales'].transform('mean') / 20  # Предполагаем 20 рабочих дней в месяце

# Вычисляем упущенные продажи
data['missed_sales'] = data['avg_daily_sales'] * (1 - (data['stock'] > 0).astype(int))

# Прогнозируем продажи на следующий месяц
next_month = pd.date_range(start=data['date'].max() + pd.Timedelta(days=1), periods=30, freq='D').to_frame(index=False, name='date')
next_month['month'] = next_month['date'].dt.to_period('M')
next_month['day_of_week'] = next_month['date'].dt.dayofweek
next_month = next_month[next_month['day_of_week'] < 5]  # Убираем выходные

# Объединяем с сезонными коэффициентами
next_month = next_month.merge(seasonal_factors, on='product', how='cross')

# Прогнозируем продажи с учетом сезонности и упущенных продаж
next_month['sales_forecast'] = (data.groupby('product')['avg_daily_sales'].mean().values *
                                 next_month['seasonal_factor']).fillna(0)

# Оставляем только необходимые колонки
result = next_month[['product', 'date', 'sales_forecast']]
result.rename(columns={'sales_forecast': 'day sales'}, inplace=True)

# Преобразуем продажи в целые положительные числа
result['day sales'] = result['day sales'].apply(np.ceil).astype(int)

# Выводим результат
print(result)
