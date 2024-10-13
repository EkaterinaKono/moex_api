import requests
import json
import pandas as pd
import flet as ft
import matplotlib
import matplotlib.pyplot as plt
from flet.matplotlib_chart import MatplotlibChart
from simpledt import CSVDataTable
import time
import datetime
from model import SearchData


matplotlib.use("svg")

'''URL для дальнейшего формирования запросов'''

BASE_SHARE_URL = 'https://iss.moex.com/iss/history/engines/stock/markets/shares/boards/TQBR/securities'

BASE_CORP_BOND_URL = 'https://iss.moex.com/iss/history/engines/stock/markets/bonds/boards/TQCB/securities'

BASE_OFZ_URL = 'https://iss.moex.com/iss/history/engines/stock/markets/bonds/boards/TQOB/securities'


def main(page: ft.Page):

    page.padding = 20

    def show_button_clicked(e):

        '''Функция, которая запускается при нажатии на кнопку Посмотреть данные.
        Сначала происходит очистка экрана. Затем валидация данных, введенных пользователем.
        Формирование URL для запросов данных по акциям, корпоративным облигациям и ОФЗ.
        Далее запрос и его обработка. Если не удалось подключиться к серверу,
        об этом выдается ошибка. Если ошибки нет, загружается json, данные обрабатываются,
        формируется файл csv. На экран выводится таблица с данными по финансовому инструменту за выбранный период.'''

        nonlocal charts

        '''Очистка экрана:'''

        page.clean()
        charts.controls.clear()
        page.add(
            ft.Row(
                [
                    securities_dropdown,
                    security_code,
                    period_text1,
                    calendar1,
                    period_text2,
                    calendar2,
                    clean_checkbox], alignment=ft.MainAxisAlignment.START
            ),
            ft.Row(
                [show_button,
                 line_chart_button,
                 bar_chart_button
                 ], alignment=ft.MainAxisAlignment.START
            )
        )
        page.theme = ft.Theme(color_scheme_seed="blue")
        time.sleep(0.5)
        clean_checkbox.value = False
        page.update()

        '''Валидация введенных пользователем данных:'''

        try:
            search_data = SearchData(
                search_security=securities_dropdown.value,
                security_code=security_code.value,
                date1=date1.value,
                date2=date2.value
            )

            '''Формирование URL для запросов'''

            if securities_dropdown.value == 'Акции':
                security_url = (BASE_SHARE_URL +
                                f'/{security_code.value}.json?from='
                                f'{date1.value.strftime('%Y-%m-%d')}&till={date2.value.strftime('%Y-%m-%d')}')
            elif securities_dropdown.value == 'Корпоративные облигации':
                security_url = (BASE_CORP_BOND_URL +
                                f'/{security_code.value}.json?from='
                                f'{date1.value.strftime('%Y-%m-%d')}&till={date2.value.strftime('%Y-%m-%d')}')
            else:
                security_url = (BASE_OFZ_URL +
                                f'/{security_code.value}.json?from='
                                f'{date1.value.strftime('%Y-%m-%d')}&till={date2.value.strftime('%Y-%m-%d')}')

            '''Запрос и сообщение об ошибке, если не удалось подключиться к серверу:'''

            try:
                response = requests.get(security_url)
            except:
                error_text = ft.Text('Не удалось подключиться к серверу. Повторите попытку позже',
                                     color='red', size=20)
                page.add(error_text)
                page.update()
            else:

                '''Выгрузка данных в JSON. Обработка данных с помощью библиотеки pandas:'''

                result = json.loads(response.text)
                if result['history.cursor']['data'][0][1] == 0:
                    text_error = ft.Text('Указан неверный код бумаги',
                                         color='red', size=20)
                    page.add(text_error)
                    page.update()
                    pass
                else:
                    columns_name = result['history']['columns']
                    resp_data = result['history']['data']
                    data_securities = pd.DataFrame(resp_data, columns=columns_name)
                    a = len(resp_data)

                    b = 100
                    while a == 100:
                        url_next_page = security_url + (f'/{security_code.value}.json?from={date1.value.strftime('%Y-%m-%d')}'
                                                        f'&till={date2.value.strftime('%Y-%m-%d')}&start={b}')
                        response = requests.get(url_next_page)
                        result = json.loads(response.text)
                        resp_data = result['history']['data']
                        data_next_page = pd.DataFrame(resp_data, columns=columns_name)
                        data_securities = pd.concat([data_securities, data_next_page], ignore_index=True)
                        a = len(resp_data)
                        b = b + 100

                    pure_data_securities = data_securities[['TRADEDATE', 'OPEN', 'LOW', 'HIGH', 'CLOSE', 'VALUE']]
                    pure_data_securities.index.name = 'NUMBER'

                    '''Формирование csv файла:'''

                    pure_data_securities.to_csv('data_securities.csv', sep=';')

                    '''Выгрузка csv в DataTable:'''

                    data_securities_csv = CSVDataTable("data_securities.csv", delimiter=";")
                    datatable = data_securities_csv.datatable

                    '''Вывод названия бумаги и таблицы с данными по ней на экран:'''

                    security_name = ft.Text(f'{result['history']['data'][0][2]}', text_align=ft.TextAlign.CENTER,
                                            size=20, weight=ft.FontWeight.BOLD)

                    my_lv = ft.ListView(expand=1, auto_scroll=True, padding=10,
                                        on_scroll_interval=1, controls=[datatable])
                    page.add(ft.Row([
                        security_name], alignment=ft.MainAxisAlignment.CENTER)
                    )
                    page.add(my_lv)
                    page.add(
                        ft.Row([charts])
                    )
                    page.update()

        except Exception as ex:
            page.add(ft.Text(f"Error: {ex}", color=ft.colors.RED))

    def line_chart_button_clicked(e):

        '''Функция, отрабатывающая нажатие на кнопку Построить график изменения цен.
        Линейный график изменения цен выводится на экран.'''

        data = pd.read_csv('data_securities.csv', sep=';')
        data["TRADEDATE"] = pd.to_datetime(data["TRADEDATE"])

        date = data['TRADEDATE']
        price = data["CLOSE"]

        fig, ax = plt.subplots(figsize=(20, 10))
        ax.plot(date, price)
        plt.xlabel('Дата', fontsize=25, loc='right')

        if securities_dropdown.value == 'Акции':
            plt.ylabel('Цена, руб', fontsize=25, loc='top')
        else:
            plt.ylabel('Цена, % от номинала', fontsize=25, loc='top')
        ax.tick_params(labelsize=20)

        charts.controls.append(MatplotlibChart(fig,expand=True))

        page.update()

    def bar_chart_button_clicked(e):

        '''Функция вызывается при нажатии на кнопку Построить график объемов торгов.
        На экран выводится столбчатая диаграмма.'''

        data = pd.read_csv('data_securities.csv', sep=';')
        volume = data['VALUE']
        data["TRADEDATE"] = pd.to_datetime(data["TRADEDATE"])
        date = data['TRADEDATE']

        fig, ax = plt.subplots(figsize=(20, 10))

        plt.bar(date, volume/1000000, width=1, edgecolor="white", linewidth=0.7)

        plt.xlabel('Дата', fontsize=25, loc='right')
        plt.ylabel('Объем, млн руб', fontsize=25, loc='top')
        ax.tick_params(labelsize=20)

        charts.controls.append(MatplotlibChart(fig, expand=True))

        page.update()

    def clean_checkbox_clicked(e):

        '''Функция, которая вызывается при установке флага Очистить всё.
        Производится очистка экрана'''

        page.clean()
        securities_dropdown.value = ''
        security_code.value = ''
        charts.controls.clear()
        calendar1.text = ' '
        calendar2.text = ' '
        date1.value = ''
        date2.value = ''

        page.add(
            ft.Row(
                [
                    securities_dropdown,
                    security_code,
                    period_text1,
                    calendar1,
                    period_text2,
                    calendar2,
                    clean_checkbox], alignment=ft.MainAxisAlignment.START
            ),
            ft.Row(
                [show_button,
                 line_chart_button,
                 bar_chart_button
                 ], alignment=ft.MainAxisAlignment.START
            )
        )
        page.theme = ft.Theme(color_scheme_seed="blue")
        time.sleep(0.5)
        clean_checkbox.value = False
        page.update()

    def date_determination1(e):

        '''Установка даты начала периода'''

        calendar1.text = f"{e.control.value.strftime('%Y-%m-%d')}"
        calendar1.update()

    def date_determination2(e):

        '''Установка даты конца периода'''

        calendar2.text = f"{e.control.value.strftime('%Y-%m-%d')}"
        calendar2.update()

    '''Controls:'''

    page.title = "Выгрузка данных по API Московской биржи"

    securities_dropdown = ft.Dropdown(hint_text='Выберите вид бумаг',
                                      options=[
                                          ft.dropdown.Option('Акции'),
                                          ft.dropdown.Option('Корпоративные облигации'),
                                          ft.dropdown.Option('ОФЗ')
                                      ], width=300
                                      )
    security_code = ft.TextField(label='Укажите код бумаги', width=300)

    date1 = ft.DatePicker(
        first_date=datetime.datetime(year=1992, month=1, day=1),
        last_date=datetime.datetime.today(),
        on_change=date_determination1
    )

    date2 = ft.DatePicker(
        first_date=datetime.datetime(year=1992, month=1, day=1),
        last_date=datetime.datetime.today(),
        on_change=date_determination2
    )

    calendar1 = ft.ElevatedButton(text=' ',
                                 icon=ft.icons.CALENDAR_MONTH_SHARP,
                                 on_click=lambda e: page.open(date1))

    calendar2 = ft.ElevatedButton(text=' ',
                                 icon=ft.icons.CALENDAR_MONTH,
                                 on_click=lambda e: page.open(date2))

    show_button = ft.ElevatedButton('Посмотреть данные', on_click=show_button_clicked)

    line_chart_button = ft.ElevatedButton('Построить график изменения цен', on_click=line_chart_button_clicked)

    bar_chart_button = ft.ElevatedButton('Построить график объемов торгов', on_click=bar_chart_button_clicked)

    clean_checkbox = ft.Checkbox(label='Очистить всё', value=False, on_change=clean_checkbox_clicked)

    charts = ft.GridView(
        expand=1,
        runs_count=2,
        max_extent=1000,
        child_aspect_ratio=2,
        spacing=5,
        run_spacing=5,
        padding=10
    )

    period_text1 = ft.Text('Период с:')
    period_text2 = ft.Text('по:')

    page.add(
        ft.Row(
            [
                securities_dropdown,
                security_code,
                period_text1,
                calendar1,
                period_text2,
                calendar2,
                clean_checkbox], alignment=ft.MainAxisAlignment.START
        ),
        ft.Row(
            [show_button,
             line_chart_button,
             bar_chart_button
             ], alignment=ft.MainAxisAlignment.START
        )
    )

    page.theme = ft.Theme(color_scheme_seed="blue")
    page.update()


ft.app(target=main)
