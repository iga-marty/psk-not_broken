from flask import render_template, request
from werkzeug.exceptions import BadRequestKeyError

from app import app, newcalc
from app.forms import PSKForm


@app.route('/')
@app.route('/index', methods=['GET', 'POST'])
@app.route('/psk', methods=['GET', 'POST'])
def psk():
    form = PSKForm()
    return render_template('psk.html', title='PSK', form=form)


def get_postpone_value(val):
    return True if val in ['yes', 'y', True, 'true'] else False

@app.route("/echo", methods=['POST'])
def echo():
    form = request.form
    card = form['card']
    card_comm = form['card_comm']
    sum_card_comm = form['sum_card_comm']
    try:
        card_comm_postpone = get_postpone_value(form['card_comm_postpone'])
    except BadRequestKeyError:
        card_comm_postpone = False
    dtstart = form['dtstart']
    pday = form['pday']
    rt = form['rt']
    mat = form['mat']
    sm = form['sm']
    strah = form['strah']

    psk, pskdv, tab, rt, strsum = newcalc.graph(float(sm), int(mat), float(rt.replace(',', '.')) / 100,
                                                       newcalc.check_start(dtstart), newcalc.check_day(pday),
                                                       newcalc.typ_cred(card), int(card_comm),
                                                       float(sum_card_comm), bool(card_comm_postpone), float(strah))
    template_context = dict(psk=psk, pskdv=pskdv, tab=tab, rt=rt, strsum=strsum)
    return render_template('resp.html', **template_context)


@app.errorhandler(404)
def page_not_found(error):
    # note that we set the 404 status explicitly
    return render_template('404.html'), 404
