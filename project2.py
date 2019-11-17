#!/usr/bin/env python
# coding: utf-8

# <div style="border:solid green 4px; padding: 20px">Привет! Вижу, ты отлично поработал, сейчас будем проверять результат. Мои критичные комментарии ты сможешь найти в <span style='color: red;'>красных</span> блоках, замечания в <span style='color: #ebd731;'>жёлтых</span>, а рекомендации и прочую информацию - в <span style='color: green;'>зеленых</span>.</div>

# # Исследование объявлений о продаже квартир
# 
# В вашем распоряжении данные сервиса Яндекс.Недвижимость — архив объявлений о продаже квартир в Санкт-Петербурге и соседних населённых пунктов за несколько лет. Нужно научиться определять рыночную стоимость объектов недвижимости. Ваша задача — установить параметры. Это позволит построить автоматизированную систему: она отследит аномалии и мошенническую деятельность. 
# 
# По каждой квартире на продажу доступны два вида данных. Первые вписаны пользователем, вторые — получены автоматически на основе картографических данных. Например, расстояние до центра, аэропорта, ближайшего парка и водоёма. 

# ### Шаг 1. Откройте файл с данными и изучите общую информацию. 

# In[38]:


import matplotlib.pyplot as plt
import pandas as pd
import math

df = pd.read_csv('datasets/real_estate_data.csv', delimiter='\t')

print (df.info())
print (df.head(1))


# ### Вывод

# Таблица с данными сохранена в формате csv, с разделителем '\t'.
# 
# Всего в таблице 23699 строк и 22 столбца. Из всех строк нет пропусков только у 8-ти столбцов. Для всех остальных колонок данные нужно восстанавливать.
# 
# Не все типы данных определились автоматически. Например, столбец "first_day_exposition" должен иметь тип datetime, а "is_apartment" - bool. Тоже нужно исправлять.

# ### Шаг 2. Предобработка данных

# 1. Изучаем пропущенные значения. Нужно обработать следующие столбцы:
#     - [x] ceiling_height
#     - [x] floors_total
#     - [x] living_area
#     - [x] is_apartment
#     - [x] kitchen_area
#     - [x] balcony
#     - [x] locality_name
#     - [x] airports_nearest
#     - [x] cityCenters_nearest
#     - [x] parks_around3000
#     - [x] parks_nearest
#     - [x] ponds_around3000
#     - [x] ponds_nearest
#     - [x] days_exposition
# 
# Сначала обрабатываем те значения, которые легче логически заполнить
# 
# is_apartment:
# - Смотрим данные
# - Смотрим количество пропущенных значений
# - Заполняем пропуски значением "False" - оно самое логичное
# - Проверяем, что пропуски заполнились
# 
# 

# In[39]:


print (f"value_counts: \n{df['is_apartment'].value_counts()}")
print (f"\nisna count: \n{df['is_apartment'].isna().count()}")
df['is_apartment'] = df['is_apartment'].fillna(False)
print (f"\nvalue_counts: \n{df['is_apartment'].value_counts()}")


# balcony:
# - Смотрим данные
# - Заполняем пропуски значением "0.0" - оно самое логичное
# - Проверяем, что пропуски заполнились

# In[40]:


print (f"value_counts: \n{df['balcony'].value_counts()}")
print (f"\nisna count: \n{df['balcony'].isna().sum()}")
df['balcony'] = df['balcony'].fillna(0.0)
print (f"\nvalue_counts: \n{df['balcony'].value_counts()}")
print (f"\nisna count: \n{df['balcony'].isna().sum()}")


# days_exposition:
# 
# У некоторых квартир не заполен столбец "days_exposition" (сколько дней было размещено объявление), однако, у всех заполнен "last_price" - значит, 
# все квартиры были сняты с публикации, и пропуски в столбце "days_exposition" можно заполнить. Заполнение будет происходить в зависимости от даты публикации. 
# Для каждого пропуска каждой даты будем высчитывать медианное значение заполненных дат.
# 
# Перед заполнением пропусков в столбце "days_exposition" нужно перевести столбец "first_day_exposition" в дату, т.к. первый зависит от второго.

# In[41]:


df['first_day_exposition'] = pd.to_datetime(df['first_day_exposition'], format='%Y-%m-%dT%H:%M:%S')

def get_median_days_exposition(df):
    """Функция заполнения количества дней размещения медианным значением"""
    years = pd.DatetimeIndex(df['first_day_exposition']).year.value_counts().index
    monthes = pd.DatetimeIndex(df['first_day_exposition']).month.value_counts().index

    for year in years:
        for month in monthes:
            median = df[(df['days_exposition'].notna()) & (pd.DatetimeIndex(df['first_day_exposition']).year == year) & (pd.DatetimeIndex(df['first_day_exposition']).month == month)]['days_exposition'].median()
            if math.isnan(median):
                median = df[(df['days_exposition'].notna()) & (pd.DatetimeIndex(df['first_day_exposition']).year == year)]['days_exposition'].median()
            df.loc[((df['days_exposition'].isna()) & (pd.DatetimeIndex(df['first_day_exposition']).year == year) & (pd.DatetimeIndex(df['first_day_exposition']).month == month)), 'days_exposition'] = median
            
    return df

print ("Заполняем пропуски в столбце \"days_exposition\"\nВсего пропусков: ")
print (df['days_exposition'].isna().sum())
df = get_median_days_exposition(df)

print ("\nПроверяем, что пропуски заполнились: ")
print (df['days_exposition'].isna().sum())


# <div style="border:solid green 4px; padding: 20px">Хорошо.</div>

# living_area:
# - Проверяем количество пропусков
# - Ищем зависимости между общей площадью и жилой
# - Заполняем пропуски
# - Проверяем, что пропуски заполнились

# In[42]:


print (f"isna sum: {df['living_area'].isna().sum()}")
print ("\nИщем зависимости между общей площадью и другими параметрами:")
#print (df[df['living_area'].notna()]['living_area'].corr(df[df['total_area'].notna()]['total_area']))
#print (df[df['living_area'].notna()]['living_area'].corr(df[df['rooms'].notna()]['rooms']))
       
print (df.corr()['living_area'].reset_index(name='correlation'))


# <div style="border:solid #ebd731; 4px; padding: 20px">Корреляции удобно смотреть вкупе, изобразив матрицу корреляций.
# </div><br>
# <font color="green">Исправлено</font>

# <div style="border:solid #ebd731; 4px; padding: 20px">Имел ввиду визуализацию. Как <a href = "https://towardsdatascience.com/better-heatmaps-and-correlation-matrix-plots-in-python-41445d0f2bec">здесь</a>.</div>

# Обнаружена прямая зависимость между жилой площадью и общей площадью: коэффициент корреляции 0.93<br>
# Обнаружена прямая зависимость между жилой площадью и количеством комнат: коэффициент корреляции 0.84<br>
# Обнаружена прямая зависимость между жилой площадью и ценой квартиры: коэффициент корреляции 0.56
# 
# Первые два параметра достаточно сильные, пропуски можно заполнить, опираясь только на них.<br>
# Заполним пропуски: сначала по общей площади, после по жилой:

# In[43]:


def get_median_living_area(df):
    """Функция заполнения пропусков в жилой площади медианным значением"""
    areas = df['total_area'].value_counts().index
    for area in areas:
        median = df[((df['living_area'].notna()) & (df['total_area'] == area))]['living_area'].median()
        df.loc[((df['living_area'].isna()) & (df['total_area'] == area)), 'living_area'] = median
    
    rooms = df['rooms'].value_counts().index
    for room in rooms:
        median = df[((df['living_area'].notna()) & (df['rooms'] == room))]['living_area'].median()
        df.loc[((df['living_area'].isna()) & (df['rooms'] == room)), 'living_area'] = median
    
    return df

df = get_median_living_area(df)
print ("\nПроверяем, что пропуски заполнились ")
print (f"isna sum: {df['living_area'].isna().sum()}")


# Теперь на основе жилой площади можно заполнить площадь кухни. 
# Делим всю жилую площадь на 10 квантилей, ищем медианное значение и заполняем пропуски
# 
# kitchen_area:
# - Проверяем количество пропусков
# - Заполняем пропуски
# - Проверяем, что пропуски заполнились

# In[44]:


print (f"isna sum: {df['kitchen_area'].isna().sum()}")

def get_median_kitchen_area(df):
    df.sort_values(by='living_area', inplace=True)
    df['quantile_areas'] = pd.qcut(df['living_area'], 10, labels=False)
    areas = df['quantile_areas'].value_counts().index
    for area in areas:
        median = df[(df['kitchen_area'].notna()) & (df['quantile_areas'] == area)]['kitchen_area'].median()
        df.loc[(df['kitchen_area'].isna()) & (df['quantile_areas'] == area), 'kitchen_area'] = median
    
    return df

df = get_median_kitchen_area(df)
print ("\nПроверяем, что пропуски заполнились: ")
print (f"isna sum: {df['kitchen_area'].isna().sum()}")


# Смотрим, сколько всего этажей в домах. На первый взгляд этажей много, как проследить зависимость от других параметров - хз. Обычно, количество этажей дома не зависит от чего-либо. В одном доме могут быть разные квартиры - однушки, трешки, разной площади и с разными балконами. К сожалению, в представленной выборке нет связей квартиры с домом - иначе, можно было бы легко заполнить пропуски. Чтобы не было пропусков, заполним их средней температурой по больнице и приведем к целому типу.
# 
# floors_total:
# - Смотрим, сколько всего этажей в домах
# - Заполняем пропуски средней температурой по больнице
# - Проверяем, что пропуски заполнились

# In[45]:


print (f"isna sum: {df['floors_total'].isna().sum()}")
print (df[df['floors_total'].notna()]['floors_total'].value_counts())
floors_total_mean = df[df['floors_total'].notna()]['floors_total'].mean()
df['floors_total'] = df.fillna(floors_total_mean)
df['floors_total'] = df['floors_total'].astype(int)
print ("\nПроверяем, что пропуски заполнились: ")
print (f"isna sum: {df['floors_total'].isna().sum()}")


# Высота потолков не зависит от этажности дома или от площади. Она напрямую зависит от класса. Если дом высокого класса и комфорта, то потолки будут высокие. Если же стандартный класс - то потолки будут стандартно 2.67 - 2.72. Попробуем привязаться к цене дома. Посмотрим, насколько потолок зависит от цены:
# 

# In[46]:


print (df[df['ceiling_height'].notna()]['ceiling_height'].corr(df[df['ceiling_height'].notna()]['last_price']))


# Как видно, коэффициент корреляции стремится к нулю, следовательно, эти величины практически не связаны.
# 
# Посмотрим среднюю высоту потолков по всем домам в выборке:

# In[47]:


print (f"Средняя: {df[df['ceiling_height'].notna()]['ceiling_height'].mean().round(2)}")
print (f"Медианная: {df[df['ceiling_height'].notna()]['ceiling_height'].median()}")


# Средний показатель что-то слишком высокий. Запоним пропуски медианным:

# In[48]:


print (f"isna sum: {df['ceiling_height'].isna().sum()}")
df['ceiling_height'] = df['ceiling_height'].fillna(df['ceiling_height'].median())
print ("\nПроверяем, что пропуски заполнились: ")
print (f"isna sum: {df['ceiling_height'].isna().sum()}")


# Оставшиеся пропуски - данные о местоположении, парках и водоемах поблизости. Эти значения не зависят от других величин. Добавим информацию о том, что для них значение не опредлено.

# In[49]:


df['locality_name'] = df['locality_name'].fillna('undefined')
df['airports_nearest'] = df['airports_nearest'].fillna(-999.99)
df['cityCenters_nearest'] = df['cityCenters_nearest'].fillna(-999.99)
df['parks_around3000'] = df['parks_around3000'].fillna(-999.99)
df['parks_nearest'] = df['parks_nearest'].fillna(-999.99)
df['ponds_nearest'] = df['ponds_nearest'].fillna(-999.99)

print ("\nЗаменяем поле last_price на тип int")
df['last_pice'] = df['last_price'].astype(int)
df.loc[df['last_pice'] <= 0, 'last_pice'] = df['last_price'].median().astype(int)

print ("\nЗаодно почистим значения в единственном строковом столбце")       
df['locality_name'] = df['locality_name'].str.strip().str.lower()

print ("\nПроверяем, что все данные заполнились:")
print (df.info())
       


# ### Шаг 3. Посчитайте и добавьте в таблицу

# In[50]:


print ("\nРассчитываем цену квадратного метра: last_price / total_area")
df['square_meter_price'] = df['last_price'] / df['total_area']
print ("\nРассчитываем день недели, месяц и год публикации объявления")
df['day_exposition'] = pd.DatetimeIndex(df['first_day_exposition']).weekday
df['month_exposition'] = pd.DatetimeIndex(df['first_day_exposition']).month
df['year_exposition'] = pd.DatetimeIndex(df['first_day_exposition']).year
print ("\nРассчитываем этаж квартиры: Первый, последний, другой")

def get_flat_floor (rows):
    floor = rows[0]
    floors_total = rows[1]
    if floor == 1:
        return 'первый'
    elif floor == floors_total:
        return 'последний'
    return 'другой'

df['floor_kind'] = df[['floor', 'floors_total']].apply(get_flat_floor, axis=1)
print ("\nПроверяем, что данные заполнились: ")
print (df['floor_kind'].value_counts())
print ("\nРасчитываем соотношение жилой площади к общей.")
df['living_to_total_area'] = df['living_area'] / df['total_area']
print ("\nРасчитываем соотношение площади кухни к общей площади.")
df['living_to_total_area'] = df['kitchen_area'] / df['total_area']


# ### Шаг 4. Проведите исследовательский анализ данных и выполните инструкции:

# <div style="border:solid #ebd731; 4px; padding: 20px">Повторяемость кода. Можно использовать лаконичную, универсальную заготовку (циклом пройтись и построить все необходимые диаграммы), а затем уже нужные рассматривать в приближении.</div><br>
# <font color="green">Исправлено</font>

# In[51]:


"""Строим гистограммы и удивляемся значениям"""

def print_hist_plots(df, columns, bins, ranges, ylims, titles):
    """Печать гистограмм с заданными параметрами"""
    for i in range(0, len(columns)):
        print (df[columns[i]].plot(
            kind='hist', 
            bins=bins[i], 
            range=ranges[i],
            ylim=ylims[i],
            title=titles[i]
        ))
        plt.show()
    return

print_hist_plots(
    df, 
    ['total_area', 'last_price', 'rooms', 'ceiling_height'],
    [100, 100, 10, 20],
    [(0, 400), (0, 40000000), (0, 9), (2.25, 4)],
    [None, None, None, None],
    [
        'Гистограмма зависимости площади квартиры от количества продаж',
        'Гистограмма зависимости цены квартиры от количества продаж',
        'Гистограмма зависимости числа комнат в квартире от количества продаж',
        'Гистограмма зависимости высоты потолков в квартире от количества продаж',
    ]
)


# Изучаем время продажи квартиры:

# In[52]:


print (f"\nСреднее время продажи квартиры: {df['days_exposition'].mean()}")
print (f"\nМедианное время продажи квартиры: {df['days_exposition'].median()}\n")
       
print_hist_plots(
    df, 
    ['days_exposition'],
    [100],
    [(0, 600)],
    [None],
    [
        'Гистограмма зависимости времени продажи квартиры от количества продаж',
    ]
)


# Обычно квартира либо продается сразу, либо в течении 3-х месяцев (90 дней). На гистограмме видно, что после 90-100 дней идет спад количества проданных квартир. "Хвост" тянется очень далеко, примерно на 600 днях его можно обрубить - дальше нет смысла рассматривать значения.

# Убираем хвосты и выбивающиеся значения у диаграмм выше:

# In[53]:


print_hist_plots(
    df, 
    ['total_area', 'last_price', 'rooms', 'ceiling_height', 'days_exposition'],
    [80, 30, 5, 10, 80],
    [(0, 150), (0, 15000000), (0, 5), (2.25, 3.25), (0, 300)],
    [(0, 1100), None, None, None, (0, 600)],
    [
        'Гистограмма зависимости площади квартиры от количества продаж',
        'Гистограмма зависимости цены квартиры от количества продаж',
        'Гистограмма зависимости числа комнат в квартире от количества продаж',
        'Гистограмма зависимости высоты потолков в квартире от количества продаж',
        'Гистограмма зависимости срока продажи квартиры от количества продаж'
    ]
)


# На гистограммах выше обнаружены следующие зависимости:
# 1. Лучше всего продаются квартиры с площадью от 35 до 60 м^2
# 2. Больше всего квартир с ценой от 2.5 до 7 миллионов.
# 3. Больше всего пользуются спросом 1,2 и 3-х комнатные квартриры. Реже 4-х.
# 4. Самая популярная высота потолков 2.5 - 2.8. Наши предположения подтвердились.
# 5. Большинство квартир продается довольно быстро. от 0 до 100-150 дней.

# Изучаем, какие факторы влияют на стоимость квартиры:

# In[54]:


print ("Зависимость цены от квадратного метра: ")
print (df['last_price'].corr(df['square_meter_price']))
print ("Зависимость цены от этажа: ")
df['floor_kind_category'] = df['floor_kind'].astype('category').cat.codes
print (df['last_price'].corr(df['floor_kind_category']))
print ("Зависимость цены от количества комнат: ")
print (df['last_price'].corr(df['rooms']))
print ("Зависимость цены от удаленности от цента: ")
print (df['last_price'].corr(df[df['cityCenters_nearest'] != -999.99]['cityCenters_nearest']))
print ("Зависимость цены от дня публикации: ")
print (df['last_price'].corr(df['day_exposition']))
print ("Зависимость цены от месяца публикации: ")
print (df['last_price'].corr(df['month_exposition']))
print ("Зависимость цены от года публикации: ")
print (df['last_price'].corr(df['year_exposition']))


# Цена квартиры напрямую зависит от цены квадратного метра.
# Так же прослеживается зависимость от количества комнат.
# 
# От остальных вышерпдеставленных параметров цена не зависит - коэффициент корреляции меньше 0.1 и стремится к нулю.

# 10 населенных пунктов с наибольшим числом объявлений:

# In[55]:


top_ads = df.groupby('locality_name')['last_price'].count().reset_index(name='count').sort_values(['count'], ascending=False).head(10)
top_ads


# Средняя цена за метр в этих районах:

# In[56]:


def get_mean_square_price(row):
    return df[df['locality_name'] == row]['square_meter_price'].median().astype(int)

top_ads['mean_square_price'] = top_ads['locality_name'].apply(get_mean_square_price)
top_ads


# Хорошо, что не стали заполнять пропущенные значения в "locality_name" по стоимости жилья. Пушкин недалеко ушел от Питера по цене.
# 
# Выделяем населенные пункты с самой высокой и самой низкой стоимостью жилья:

# In[57]:


print (f"Самая высокая стоимость жилья в населенном пункте \"{top_ads.sort_values(by='mean_square_price', ascending=False).head(1)['locality_name'].to_string(index=False)}\"")
print (f"Самая низкая стоимость жилья в населенном пункте \"{top_ads.sort_values(by='mean_square_price').head(1)['locality_name'].to_string(index=False)}\"")
       


# ### Ищем центр Санкт-Петербурга
# 
# Отфильтруем данные по местоположению "Санкт-Петербург":

# In[58]:


spb_data = df[(df['locality_name'] == 'санкт-петербург') & (df['cityCenters_nearest'] != -999.99)]
spb_data.reset_index(drop=True, inplace=True)


# Округляем расстояние до центра:

# In[59]:


spb_data['cityCenters_nearest'] = spb_data['cityCenters_nearest'].astype(int)


# Считаем среднюю цену для каждого километра:

# In[60]:


def get_mean_per_m(row):
    return spb_data[spb_data['cityCenters_nearest'] == row]['last_price'].median().astype(int)

meters = spb_data['cityCenters_nearest'].value_counts().index
df_meters = pd.DataFrame({'meters': meters})
df_meters['city_price_mean'] = df_meters['meters'].apply(get_mean_per_m)
df_meters['city_price_mean'].head()


# Построим график, чтобы понять где сильно мемняется цена - ищем центр с города с мажорскими ценами

# <div style="border:solid green 4px; padding: 20px">Не километры, метры.</div><br>
# <font color="green">Исправлено</font>

# In[62]:


df_meters.plot(
    kind='scatter',
    x='meters',
    y='city_price_mean',
    title='Зависимость стоимости от расстояния до центра'
)


# График резко меняется на значении x=7500. Значит, в центр входят все квартиры, у которых расстояне до центра меньше, чем 7500

# <div style="border:solid green 4px; padding: 20px">Аналогично, повторяемость. Про матрицу я упоминал. Пример есть в Slack.</div><br>
# <font color="green">Исправлено</font>

# ### Изучаем зависимости квартир в центральном районе:

# In[75]:


spb_center = spb_data[spb_data['cityCenters_nearest'] < 7500]
spb_center.reset_index(drop=True, inplace=True)

def get_median(df, columns, names):
    print ("\n")
    for i in range(0, len(columns)):
        print (f"Медиана {names[i]}: {df[columns[i]].median().round(3)}")
    return 

print ("\nЦентр Санкт-Петербурга:")
print (spb_center.corr()['last_price'].reset_index(name='correlation'))
get_median(
    spb_center,
    [
        'last_price',
        'ceiling_height',
        'living_area',
        'kitchen_area',
        'rooms',
    ],
    [
        'цены квартиры',
        'высоты потолков',
        'жилой площади',
        'площади кухни',
        'количества комнат',
    ]
)

print ("\n\nВесь город: ")
print (spb_data.corr()['last_price'].reset_index(name='correlation'))
get_median(
    spb_data,
    [
        'last_price',
        'ceiling_height',
        'living_area',
        'kitchen_area',
        'rooms',
    ],
    [
        'цены квартиры',
        'высоты потолков',
        'жилой площади',
        'площади кухни',
        'количества комнат',
    ]
)


# Как видим, общие показатели зависимости параметров практически не отличаются. Переведем выше полученные показатели в удобочитаемую таблицу:

# In[76]:


names = [
    'Зависимость цены от квадратного метра', 
    'Зависимость цены от этажа', 
    'Зависимость цены от количества комнат', 
    'Зависимость цены от удаленности от цента',
    'Зависимость цены от высоты потолков',
    'Зависимость цены от дня публикации',
    'Зависимость цены от месяца публикации',
    'Зависимость цены от года публикации',
    'Медиана цены квартиры',
    'Медиана высоты потолков',
    'Медиана жилой площади',
    'Медиана площади кухни',
    'Медиана количества комнат',
]

city_total_spb = { 
    'spb_total': [0.76, -0.03, 0.37, -0.25, 0.06, 0.00, 0.00, -0.04, 5500000.0, 2.65, 31.2, 9.7, 2.0],
    'spb_center': [0.79, -0.06, 0.31, -0.04, 0.07, 0.02, -0.01, -0.04, 9200000.0, 2.8, 46.0, 11.9, 3.0]
}

compare_df = pd.DataFrame(city_total_spb, index=names)
compare_df['difference'] = (compare_df['spb_total'] - compare_df['spb_center']).round(2)
compare_df


# Построим графики зависимости вышеописанных параметров, чтобы лучше понимать что на что влияет:

# In[77]:


print_hist_plots(
    spb_center, 
    ['last_price', 'rooms', 'ceiling_height', 'days_exposition'],
    [30, 5, 10, 50],
    [(0, 15000000), (0, 5), (2.25, 3.25), (0, 300)],
    [None, None, None, (0, 200)],
    [
        'Гистограмма зависимости цены квартиры от количества продаж',
        'Гистограмма зависимости числа комнат в квартире от количества продаж',
        'Гистограмма зависимости высоты потолков в квартире от количества продаж',
        'Гистограмма зависимости срока продажи квартиры от количества продаж'
    ]
)


# ### Вывод
# На стоимость квартиры прямо и очень сильно влияют:
# 
# - Цена квадратного метра
# - Расположение квартиры
# - Количество комнат
# 
# В центре Санкт-Петербурга квартиры неоправданно дорогие. Интересное наблюдение, квартиры в таких домах, обычно, имеют высокие потолки, большую жилую площадь, большую кухню и не менее 3-х комнат. Так же, согласно последним графикам, квартиры в центре довольно быстро продаются.

# <div style="border:solid green 4px; padding: 20px">Выводы хорошие, в целом логика хороша соблюдается. Недочеты связаны с более рациональным написанием кода. Жду исправлений. Успехов!</div><br>
# <font color="green">Каждое замечание исправлено. Построены матрицы зависимостей, отрефакторен код.</font>

# <div style="border:solid green 4px; padding: 20px">Хорошо. Удачи и упорства в дальнейшем!</div><br>

# ### Шаг 5. Общий вывод

# В текущем проекте было сделано:
# 
# 1. Изучены полученные данные по квартирам
# 2. Определена работа по категоризации и восстановлению данных
# 3. Найдены закономерности в данных и заполнены все пропуски
# 4. Ни одна строчка в данных не пострадала
# 5. Построены графики зависимости цены квартиры от её параметров
# 6. Найден город с самым большим количетвом объявлений
# 7. Выделен сегмент объявлений, которые составляют центр города
# 8. Определены зависимости цены квартиры от её параметров для центра города
# 
# Определены параметры, которые прямо влияют на стоимость квартиры:
# 1. Расположение квартиры (город/пригород, центр/не центр)
# 2. Количетво комнат 
# 3. Жилай площадь
# 4. Количество комнат
# 
# Второстепенные данные, такие как "высота потолков, дата публикации" оказывают незначительное влияние на ценообразование.

# ### Чек-лист готовности проекта
# 
# Поставьте 'x' в выполненных пунктах. Далее нажмите Shift+Enter.

# - [x]  открыт файл
# - [x]  файлы изучены (выведены первые строки, метод info())
# - [x]  определены пропущенные значения
# - [x]  заполнены пропущенные значения
# - [x]  есть пояснение какие пропущенные значения обнаружены
# - [x]  изменены типы данных
# - [x]  есть пояснение в каких столбцах изменены типы и почему
# - [x]  посчитано и добавлено в таблицу: цена квадратного метра
# - [x]  посчитано и добавлено в таблицу: день недели, месяц и год публикации объявления
# - [x]  посчитано и добавлено в таблицу: этаж квартиры; варианты — первый, последний, другой
# - [x]  посчитано и добавлено в таблицу: соотношение жилой и общей площади, а также отношение площади кухни к общей
# - [x]  изучены следующие параметры: площадь, цена, число комнат, высота потолков
# - [x]  построены гистограммы для каждого параметра
# - [x]  выполнено задание: "Изучите время продажи квартиры. Постройте гистограмму. Посчитайте среднее и медиану. Опишите, сколько обычно занимает продажа. Когда можно считать, что продажи прошли очень быстро, а когда необычно долго?"
# - [x]  выполнено задание: "Уберите редкие и выбивающиеся значения. Опишите, какие особенности обнаружили."
# - [x]  выполнено задание: "Какие факторы больше всего влияют на стоимость квартиры? Изучите, зависит ли цена от квадратного метра, числа комнат, этажа (первого или последнего), удалённости от центра. Также изучите зависимость от даты размещения: дня недели, месяца и года. "Выберите 10 населённых пунктов с наибольшим числом объявлений. Посчитайте среднюю цену квадратного метра в этих населённых пунктах. Выделите населённые пункты с самой высокой и низкой стоимостью жилья. Эти данные можно найти по имени в столбце '*locality_name'*. "
# - [x]  выполнено задание: "Изучите предложения квартир: для каждой квартиры есть информация о расстоянии до центра. Выделите квартиры в Санкт-Петербурге (*'locality_name'*). Ваша задача — выяснить, какая область входит в центр. Создайте столбец с расстоянием до центра в километрах: округлите до целых значений. После этого посчитайте среднюю цену для каждого километра. Постройте график: он должен показывать, как цена зависит от удалённости от центра. Определите границу, где график сильно меняется — это и будет центральная зона. "
# - [x]  выполнено задание: "Выделите сегмент квартир в центре. Проанализируйте эту территорию и изучите следующие параметры: площадь, цена, число комнат, высота потолков. Также выделите факторы, которые влияют на стоимость квартиры (число комнат, этаж, удалённость от центра, дата размещения объявления). Сделайте выводы. Отличаются ли они от общих выводов по всему городу?"
# - [x]  в каждом этапе есть выводы
# - [x]  есть общий вывод
