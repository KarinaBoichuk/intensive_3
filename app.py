import streamlit as st
import pandas as pd
import pickle
from datetime import datetime, timedelta

# Загрузка модели
@st.cache_resource
def load_model():
    try:
        with open('armature_price_model.pkl', 'rb') as f:
            model = pickle.load(f)
        return model
    except Exception as e:
        st.error(f"Ошибка загрузки модели: {str(e)}")
        return None

# Загрузка данных
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('111updated_merged.csv', parse_dates=['dt'])
        df = df.dropna(subset=['Цена на арматуру'])
        return df.sort_values('dt')
    except Exception as e:
        st.error(f"Ошибка загрузки данных: {str(e)}")
        return None

# Найти ближайшую доступную дату
def find_nearest_date(df, target_date):
    dates = pd.Series(df['dt'].dt.date.unique())
    if target_date in dates.values:
        return target_date
    past_dates = dates[dates <= target_date]
    if not past_dates.empty:
        return past_dates.iloc[-1]
    return dates.iloc[0]

# Основной интерфейс
def main():
    st.title("📊 Прогнозирование закупок арматуры")
    
    # Загрузка данных и модели
    df = load_data()
    model = load_model()
    
    if df is None or model is None:
        st.stop()
    
    # Определение диапазона дат
    min_date = df['dt'].min().date()
    max_date = df['dt'].max().date()
    
     # Выбор даты (исправленная строка)
    selected_date = st.sidebar.date_input(
        "Выберите дату для анализа",
        value=max_date,
        min_value=min_date,
        max_value=max_date + timedelta(days=365)
    )
    
    # Находим ближайшую доступную дату
    nearest_date = find_nearest_date(df, selected_date)
    if nearest_date != selected_date:
        st.warning(f"Используем ближайшую доступную дату с данными: {nearest_date}")
    
    weekly_need = st.sidebar.number_input(
        "Недельная потребность (тонн)",
        min_value=1,
        value=100
    )
    
    # Получаем последние доступные данные
    last_data = df[df['dt'].dt.date <= nearest_date].iloc[-1]
    current_price = last_data['Цена на арматуру']
    
    # Прогнозирование
    try:
        avg_price = df['Цена на арматуру'].mean()
        
        if current_price > avg_price:
            predictions = [current_price * (1.02 ** i) for i in range(1, 7)]
            trend = "рост"
            recommended_weeks = 3
        else:
            predictions = [current_price * (0.99 ** i) for i in range(1, 7)]
            trend = "снижение"
            recommended_weeks = 1
        
        # Отображение результатов
        st.subheader("Рекомендация по закупке")
        st.success(f"Рекомендуемый объем: {recommended_weeks * weekly_need} тонн")
        st.success(f"Период закупки: {recommended_weeks} недель")
        st.info(f"Текущий тренд: {trend} цен")
        
        # График прогноза
        forecast_dates = [nearest_date + timedelta(weeks=i) for i in range(1, 7)]
        chart_data = pd.DataFrame({
            "Дата": [nearest_date] + forecast_dates,
            "Цена": [current_price] + predictions,
            "Тип": ["Факт"] + ["Прогноз"]*6
        }).set_index("Дата")
        
        st.line_chart(chart_data)
        
        # Таблица с прогнозами
        st.table(pd.DataFrame({
            "Неделя": range(1, 7),
            "Дата": forecast_dates,
            "Прогноз цены": [f"{p:.2f}" for p in predictions],
            "Изменение": [f"{((p-current_price)/current_price*100):.1f}%" for p in predictions]
        }))
        
    except Exception as e:
        st.error(f"Ошибка при формировании прогноза: {str(e)}")

if __name__ == "__main__":
    main()