# coding: UTF-8

import datetime  # инструменты для работы с датами
from datetime import timedelta  # отдельная субфункция для работы с датами, для удобства вызова

import numpy as np
import pandas as pd  # инструменты для работы с таблицами
from monthdelta import \
    monthdelta  # аналог пакета по работе с датами, ориентируется на операции с месяцами (аналог addmonths())
from pandas import Timedelta


dtshift = True


def check_start(inp):
    if inp in ['today', '']:
        output = datetime.date.today()
        return output
    else:
        try:
            output = datetime.datetime.date((datetime.datetime.strptime(inp, '%Y-%m-%d')))
            return output
        except ValueError:
            output = datetime.datetime.date((datetime.datetime.strptime(inp, '%d.%m.%Y')))
            return output


def check_day(inp):
    if inp in ['today', '']:
        output = int(datetime.date.today().day)
        return output
    else:
        output = int(inp)
        if 0 < output < 31:
            return output
        else:
            return 1


def typ_cred(inp):
    match inp:
        case 'cred':
            return 0
        case 0:
            return 0
        case 'card':
            return 1
        case 1:
            return 1


def ann(x, y, z):  # аннуитет. x - ставка, y - полный срок (формула уже учитывает сокращение на 1 месяц), z - сумма.
    return z * ((x / 12 * ((1 + x / 12) ** (y - 1))) / ((1 + x / 12) ** (y - 1) - 1))


def next_i_months(date, j):  # дата в будущем. Аналог addmonths())
    return date + monthdelta(j)


def assert_holidays(i, y, a, b):
    if i < y:
        if b in [5, 6]:
            a = a + datetime.timedelta(days=(7 - b))
    else:
        if b in [5, 6]:
            a = a + datetime.timedelta(days=-2)
    return a


def nxtdt(x, y, z, p):  # перенос даты на следующий рабочий день.
    # x - дата начала, y - полный срок,
    # z(1) - смещение на рабочий день, p - дата платежа

    lst = []
    if p > 0:
        x = datetime.date(year=x.year, month=x.month, day=p)

    for i in range(y + 1):
        a = next_i_months(x, i)
        b = datetime.datetime.weekday(a)
        if z:
            a = assert_holidays(i, y, a, b)
        lst.append(a)
    return lst


def is_leap(s):  # определение високосного года
    return (s % 4 == 0) & ((s % 100 != 0) | (s % 400 == 0))


def ldom(any_day):  # определение последнего дня месяца.
    next_month = any_day.replace(day=28) + datetime.timedelta(days=4)
    return next_month - datetime.timedelta(days=next_month.day)


def split_month(start, end):  # разделение интервала на два по концу месяца внутри интервала
    split_date = ldom(start)
    frst = split_date - start + timedelta(1)
    second = end - split_date - timedelta(1)
    return frst.days, second.days


def get_y_days_on_split(start, end):  # определение количества дней в году для корректного расчета процентов.
    if is_leap(start.year):
        firsty = 366
    else:
        firsty = 365
    if is_leap(end.year):
        secondy = 366
    else:
        secondy = 365
    return firsty, secondy



def count_proc(row, left, rt):  # счтаем проценты. Функция вызывается для точечного расчета процентов.
    if row.leapinside:
        if row.needsplit:
            print(
                "Что-то пошло не так. Внутри високосного года не может быть разделения периодов на 365/366 дней"
            )
            return 0
        else:
            a = left / 366 * rt * (row['diff'])
            if type(a) == Timedelta:
                a = a.nanoseconds
            return a
    else:
        if not row.needsplit:
            a = left / 365 * rt * (row['diff'])
            if type(a) == Timedelta:
                a = a.nanoseconds
            return a
        else:
            a = (left / get_y_days_on_split(row.prevpmt, row.payday)[0] * rt
                 * split_month(row.prevpmt, row.payday)[0]) + (
                        left / get_y_days_on_split(row.prevpmt, row.payday)[1]
                        * rt * split_month(row.prevpmt, row.payday)[1])
            if type(a) == Timedelta:
                a = a.nanoseconds
            return a


def itercred(rng, mat, sm, rt):  # итеративная функция построения графика по кредиту.
    prevost = sm
    last_i = sm
    ind = 0
    for index, row in rng.iterrows():  # итерируем строки таблицы.
        # Индекс - номер строки от 0, row - кортеж с данными по строке.
        rng.loc[index, 'proc'] = count_proc(row, last_i, rt)  # для каждой ячейки proc вычисляем величину
        # процентов.
        rng.loc[0, 'proc'] = count_proc(rng.loc[0], sm, rt)# величина процентов для первого платежа
        rng.loc[index, 'cred'] = rng.loc[index, 'annuity'] - rng.loc[index, 'proc']
        # после вычисления процентов вставляем платеж по ссуде исходя из величины аннуитета

        rng.loc[0, 'cred'] = 0  # обнуляем первый платеж по ссуде
        if rng.loc[index, 'cred'] < 0:  # проверяем, не зашкаливают ли проценты (сумма процентов больше аннуитета)
            rng.loc[index, 'cred'] = 0
        last_i = last_i - rng.loc[index, 'cred']
        if index == mat - 1:  # пишем в последний платеж по ссуде остаток невыплаченной в предыдущих периодах ссуды.
            rng.loc[index, 'cred'] = sm - rng.cred.iloc[:(mat - 1)].sum()
        rng.loc[index, 'ostout'] = prevost - rng.loc[index, 'cred']  # исходящий остаток
        prevost = rng.loc[index, 'ostout']  # предыдущий исходящий отсток
        preprevost = prevost + rng.loc[index, 'cred']
        if rng.loc[index, 'ostout'] < 0:  # продолжаем обрабатывать последний платеж
            rng.loc[index, 'cred'] = preprevost
            rng.loc[index, 'ostout'] = 0
            prevost = 0
        if (rng.loc[index, 'cred'] == 0) and (
                rng.loc[index, 'ostout'] == 0):
            rng.drop(rng.index[index], inplace=True)  # Сокращаем лишние строки снизу после выплаты всей ссуды.
            ind = index
        if ind > 0:
            rng.drop(rng.index[ind], inplace=True)  # удаляем ВСЕ строки после последней строки.
    return rng


def itercard(rng, sm, rt):  # итеративная функция построения графика по карте.
    for index, row in rng.iterrows():
        rng.loc[index, 'proc'] = count_proc(row, sm, rt)
        rng.loc[0, 'proc'] = count_proc(rng.loc[0], sm, rt)
        rng.loc[index, 'cred'] = 0
    return rng


# PSK #


def first(frm):  # дата первого платежа
    a = frm['payday'].iloc[0]
    return a


def qk(frame, base):  # коэффициент Q. Функция работает на таблице.
    # q = abs((frame['payday'] - first(frame)).dt.days // float(base))
    a = frame['payday']
    b = first(frame)
    q = abs(((a - b)/np.timedelta64(1, 'D')) // float(base))
    return q


def ek(frame, base):  # коэффициент E. Работает на таблице.
    # i, d = divmod(((frame['payday'] - first(frame)).dt.days - frame.q * float(base)) / float(base), 1)
    a = frame['payday']
    b = first(frame)
    i, d = divmod((((a - b)/np.timedelta64(1, 'D')) - frame.q * float(base)) / float(base), 1)
    e = abs(d)
    return e


def dfl(row, *rat):  # расчет дисконтированного денежного потока для каждой строки. Работат построчно.
    rate = rat[0]
    disc = row['flow'] / ((1 + row['e'] * rate) * ((1 + rate) ** row['q']))
    return disc


def dflder(row, *rat):  # расчет производной от дисконтированного денежного потока.
    rate = rat[0]
    discder = -((row['flow'] * ((rate + 1) ** -row['q'] - 1)) *
                   ((row['q'] * row['e'] * rate) - row['q'] + (row['e'] * rate))) / ((row['e'] * rate + 1) ** 2)
    return discder


def leapstart():
    return lambda row: is_leap(row.prevpmt.year)  # определяем, входит ли дата начала периода в високосный год


def leapend():
    return lambda row: is_leap(row.payday.year)  # определяем, входит ли дата конца периода в високосный год


def needsplit():
    return lambda row: row.leapend ^ row.leapstart  # нужно ли разбивать период на два с разным количеством дней в году


def leapinside():
    return lambda row: row.leapend & row.leapstart  # входит ли весь период в високосный год.


def graph(sm, mat, rt, dtstart, pday, card, card_comm, sum_card_comm, card_comm_postpone, strah):
    dtend = dtstart + monthdelta(mat)  # Дата окончания.
    dtrange = pd.DataFrame(data=nxtdt(dtstart, mat, dtshift, pday), columns=[
        'payday',])  # формируем массив dtrange со столбцом payday - дата платежа, с которым будем работать.
    dtrange.loc[0, 'payday'] = dtstart
    dtrange.loc[mat, 'payday'] = dtend  # корректируем последний платеж. Перенос на рабочий день нам не нужен.
    dtrange['prevpmt'] = dtrange.payday.shift(1).fillna(
        dtstart)  # вставляем дату предыдущего платежа. Технически мы копируем столбец payday и сдвигаем его вниз.
    dtrange.loc[0, 'prevpmt'] = dtstart
    dtrange.loc[1, 'prevpmt'] = dtstart
    dtrange = dtrange[['prevpmt', 'payday']]  # меняю столбцы местами. Мне в таком виде было удобней.
    dtrange['diff'] = pd.to_numeric((
            dtrange.payday - dtrange.prevpmt).astype('timedelta64[s]')//86400) # вычисляем длительность
    # между
    # платежами. Секунды в дни
    dtrange['leapstart'] = dtrange.apply(leapstart(), axis=1)
    dtrange['leapend'] = dtrange.apply(leapend(), axis=1)
    dtrange['needsplit'] = dtrange.apply(needsplit(), axis=1)
    dtrange['leapinside'] = dtrange.apply(leapinside(), axis=1)
    dtrange['annuity'] = 0.0
    dtrange['annuity'] = ann(rt, mat, sm)  # вставляем аннуитет.
    dtrange['ostout'] = 0.0  # дефолт для первого прохода
    dtrange['proc'] = 0.0  # дефолт для первого прохода
    dtrange['cred'] = 0.0  # дефолт для первого прохода
    dtrange['proc'] = pd.to_numeric(dtrange['proc'])
    dtrange['cred'] = pd.to_numeric(dtrange['cred'])
    dtrange.drop(dtrange.index[0], inplace=True)  # сбрасываем интекс номеров строк. Для сортировки.
    dtrange.reset_index(drop=True, inplace=True)
    dtrange.loc[0, 'proc'] = count_proc(dtrange.iloc[0], sm, rt)  # считаем проценты для первого платежа.

    # формируем платежи #
    if card == 0:  # убер-сложная логика. Никто не разберется
        dtrange = itercred(dtrange, mat, sm, rt)
    else:
        dtrange = itercard(dtrange, sm, rt)

    # noinspection PyUnresolvedReferences
    dtrange = dtrange.dropna(axis='index', how='all')  # очищаем от пустых значений (NULL)

    # Если нам необходимо добавлять прочие платежи в график (комиссии, страховки и т.п.),
    # то нужно это делать именно в этом месте.
    # Дополнительные платежи необходимо добавить в столбец flow на следующем шаге.

    # место для вашей рекламы (зачеркнуто) расчета дополнительных платежей по кредиту
    for index, row in dtrange.iterrows():  # вставляем величину потока для каждой даты.
        dtrange.loc[index, 'flow'] = dtrange.loc[index, 'cred'] + dtrange.loc[index, 'proc']
    dtrange.drop(['leapstart', 'leapend', 'needsplit', 'leapinside', 'annuity'], axis=1,
                 inplace=True)  # убираем ненужные столбцы

    # Определяем параметры расчета ПСК
    if card == 1 and card_comm == 1:
        if not card_comm_postpone:
            dtrange.flow = dtrange.flow + sum_card_comm
        if card_comm_postpone:
            dtrange.flow[13:] = dtrange.flow[13:] + sum_card_comm

    pr = 0.00000000001  # параметры сходимости. Бесконечно увеличивать смысла нет, для float расчетов этого достаточно.
    maxiter = 100  # предельное число итераций, в ходе которых должна быть достигнута целевая сходимость
    itercount = 1  # глобальная переменная
    dtrange['diff'] = dtrange['diff'].astype(int)
    nbase = dtrange['diff'].mode()  # наиболее часто встречающееся значение длительности базового периода.
    nbase = nbase[0]  # на всякий случай берем первый элемент
    if type(nbase) == Timedelta:
        nbase = nbase.nanoseconds
    cntbp = round(365 / nbase)  # число базовых периодов. Округляем до целых
    ratebp = rt / cntbp  # ставка базового периода

    # Готовим график к расчету ПСК #

    # добваляем в график еще один ряд. При расчете ПСК выдача - тоже денежный поток.
    if card_comm_postpone:
        add_comm = 0
    else:
        add_comm = sum_card_comm
    dtrange.loc[-1] = [dtstart, dtstart, 0, sm, 0, -sm, (-sm + add_comm * card_comm)]
    dtrange.index = dtrange.index + 1  # обновляем индекс
    dtrange.sort_index(inplace=True)
    if card == 1:  # Только для карт. На протяжении всего периода сумма потока включает в себя сумму кредита.
        dtrange.loc[mat, 'cred'] = sm
        dtrange.loc[mat, 'flow'] = sm + dtrange.loc[mat, 'proc']
        dtrange.insert(4, 'Комиссия', sum_card_comm)
        if card_comm_postpone:
            dtrange.loc[:13, 'Комиссия'] = 0

        # dtrange.loc[mat, 'Комиссия'] = 0
    strsum = sm * strah / 100 * 1 * mat / 12
    dtrange.flow[0] = dtrange.flow[0] + strsum
    # paste magic and unicorns here #
    while itercount <= maxiter:  # итерируем пока не будет достигнута сходимость.
        dtrange['q'] = qk(dtrange, nbase)
        dtrange['e'] = ek(dtrange, nbase)
        dtrange['disc'] = dtrange.apply(dfl, axis=1, args=(ratebp, None))
        dtrange['discder'] = dtrange.apply(dflder, axis=1, args=(ratebp, None))
        ratebpnext = ratebp - (dtrange.disc.sum() / dtrange.discder.sum())
        if itercount == 100:
            print('fail')
        if abs(dtrange.disc.sum() / dtrange.discder.sum()) <= pr:
            itercount = 101
        else:
            itercount += 1
            ratebp = ratebpnext
    pskg = round(ratebp * cntbp * 100, 3)
    pskdvg = round(dtrange.flow.sum(), 2)

    tab = dtrange
    tab = tab.drop(columns=['prevpmt', 'diff', 'q', 'e', 'disc', 'discder'])
    tab = tab.rename(index=str, columns={"payday": "Дата потока", "ostout": "Остаток долга", "proc": "Проценты",
                                         "cred": "Ссуда", "flow": "Денежный поток", })
    pd.options.display.float_format = '{: .2f}'.format

    return pskg, pskdvg, tab, rt * 100, strsum, strah
