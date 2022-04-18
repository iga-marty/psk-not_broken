from flask import render_template, request, jsonify, redirect, flash
from app import app
from app.forms import PSKForm
from app import newcalc


@app.route('/')
@app.route('/index',  methods=['GET', 'POST'])
@app.route('/psk', methods=['GET', 'POST'])
def psk():
    form = PSKForm()
    return render_template('psk.html', title='PSK', form=form)





@app.route("/echo", methods=['POST'])
def echo():

    card = request.form['card']
    card_comm = request.form['card_comm']
    sum_card_comm = request.form['sum_card_comm']
    dtStart = request.form['dtStart']
    pday = request.form['pday']
    rt = request.form['rt']
    mat = request.form['mat']
    sm = request.form['sm']
    strah = request.form['strah']

    psk, pskdv, tab, rt, strsum, strah = newcalc.graph(float(sm), int(mat), float(rt.replace(',','.'))/100, newcalc.check_start(dtStart), newcalc.check_day(pday), newcalc.typ_cred(card), int(card_comm), float(sum_card_comm), float(strah))
    template_context = dict(psk=psk, pskdv=pskdv, tab=tab, rt = rt, strsum = strsum, strah = strah)
    return render_template('resp.html', **template_context)


@app.errorhandler(404)
def page_not_found(error):
    # note that we set the 404 status explicitly
    return render_template('404.html'), 404