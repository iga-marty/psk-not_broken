# coding: UTF-8

from datetime import date

from wtforms import FloatField, Form, HiddenField, IntegerField, SelectField, SubmitField
from wtforms.fields import DateField
from wtforms.validators import DataRequired


class PSKForm(Form):
    card = SelectField('Тип кредита', choices=[('cred', 'Кредит'), ('card', 'Карта')], default='cred')
    card_comm = SelectField('Комисся', choices=[('0', 'не взымается'), ('1', 'взымается')], default='0')
    sum_card_comm = IntegerField('Сумма комиссии', default=0, validators=[DataRequired()])
    dtstart = DateField('Дата выдачи', format='%d-%m-%Y', default=date.today())
    pday = IntegerField('Дата платежа', default=date.today().day)
    rt = FloatField('Ставка', default=10.0, validators=[DataRequired()])
    mat = IntegerField('Срок в месяцах', default=12, validators=[DataRequired()])
    sm = FloatField('Сумма кредита', default=100000, validators=[DataRequired()])
    strah = FloatField('% СЖ', default=0.0)
    use_cache = HiddenField('Кэш', default=0)
    submit = SubmitField('Рассчитать')
