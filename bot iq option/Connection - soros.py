from iqoptionapi.stable_api import IQ_Option
import time
from configobj import ConfigObj
import json, sys
from datetime import datetime

config = ConfigObj('config.txt')
email = config['LOGIN']['email']
password = config['LOGIN']['password']
tipo = config['AJUSTES']['tipo']
valor_entrada = config['AJUSTES']['valor_entrada']
stop_win = float(config['AJUSTES']['stop_win'])
stop_loss = float(config['AJUSTES']['stop_loss'])
lucro_total = 0
stop = True

if config['MARTINGALE']['usar_martingale'] == 'S':
    martingale = int(config['MARTINGALE']['niveis_martingale'])
else:
    martingale = 0

fator_mg = config['MARTINGALE']['fator_martingale']

if config['SOROS']['usar_soros'] == 'S':
    soros = True
    niveis_soros = int(config['SOROS']['niveis_soros'])
    nivel_soros = 0
else:
    soros = False
    niveis_soros = 0
    nivel_soros = 0

lucro_op_atual = 0
valor_soros = 0

API = IQ_Option(email,password)

print('Iniciando conexão com a IQOption')
### conectar na IQOPTION ###
check, reason = API.connect()
if check:
    print('\nlogin realizado com sucesso!')
else:
    
    if reason == '{"code":"invalid_credentials","message":"You entered the wrong credentials. Please ensure that your login/password is correct."}':
        print('\nEmail ou senha incorreto')
        sys.exit()
    else:
        print('\nHouve um problema na conexão')
        print(reason)
        sys.exit()

### Função para Selecionar demo ou real ###
while True: 
    escolha = input('\nSelecione a conta em que deseja conectar: "demo" ou "real": ').upper()
    if escolha == 'DEMO':
        conta = 'PRACTICE'
        print('\n>> Conta demo selecionada')
        break
    if escolha == 'REAL':
        conta = "REAL"
        print('\n>> Conta real selecionada')
        break
    else:
        print('\nEscolha incorreta! Digite demo ou real - ')

API.change_balance(conta)

### Função check stop win e loss ###

def check_stop():
    global stop,lucro_total
    if lucro_total <= float('-'+str(abs(stop_loss))):
        stop = False
        print('\n***************************************')
        print('\nSTOP LOSS ',str(cifrao),str(lucro_total))
        sys.exit()

    if lucro_total >= float('-'+str(abs(stop_loss))):
        stop = False
        print('\n***************************************')
        print('\nSTOP LOSS ',str(cifrao),str(lucro_total))
        sys.exit()

### Função do melhor payout
def payout(par):
    profit = API.get_all_profit()
    all_asset = API.get_all_open_time()

    try:
        if all_asset['binary'][par]['open']:
            if profit[par]['binary'] > 0:
                binary = round(profit[par]['binary'],2) * 100
        else:
            binary = 0
    except:
        binary = 0

    try:
        if all_asset['turbo'][par]['open']:
            if profit[par]['turbo'] > 0:
                turbo = round(profit[par]['turbo'],2) * 100
        else:
            turbo = 0
    except:
        turbo = 0

    try:
        if all_asset['binary'][par]['open']:
            digital = API.get_digital_payout(par)
        else:
            digital = 0
    except:
        digital = 0
    
    return binary,turbo,digital


### Função abrir ordem e checar resultado ###
def compra(ativo,valor_entrada,direcao,exp,tipo):
    global stop,lucro_total, nivel_soros,niveis_soros, valor_soros, lucro_op_atual

    if soros:
        if nivel_soros == 0:
            entrada = valor_entrada

        if nivel_soros >= 1 and valor_soros > 0 and nivel_soros <= niveis_soros:
            entrada = valor_entrada + valor_soros

        if nivel_soros > niveis_soros:
            lucro_op_atual = 0
            valor_soros = 0
            entrada = valor_entrada
            nivel_soros = 0
    else:
        entrada = valor_entrada


    for i in range(martingale +1):

        if stop == True:

            if tipo == 'digital':
                check, id = API.buy_digital_spot_v2(ativo,entrada,direcao,exp)
            else:
                check, id = API.buy(entrada,ativo,direcao,exp)

            if check:
                if i == 0:
                    print('\nOrdem Aberta \n >>Ativo: ',ativo,'\n >>Valor: ',cifrao,entrada,'\n >>tempo: ',exp,'min')
                if i >= 1:
                    print('\nOrdem Aberta para gale',str(i),'\n >>Ativo: ',ativo,'\n >>Valor: ',cifrao,entrada,'\n >>tempo: ',exp,'min')

                while True:
                    time.sleep(0.1)
                    status, resultado = API.check_win_digital_v2(id) if tipo == 'digital' else API.check_win_v4(id)

                    if status:

                        lucro_total += round(resultado,2)
                        valor_soros += round(resultado,2)
                        lucro_op_atual += round(resultado,2)
                        if resultado > 0:
                            if i == 0:
                                print('\n\nResultado: ',ativo,' WIN','\nLucro: ',cifrao, round(resultado,2),'\n >> Lucro total: ',cifrao,round(lucro_total,2))
                            if i >= 1:
                                print('\n\nResultado no gale: ',str(i),' WIN ',ativo,'\nLucro: ',cifrao, round(resultado,2),'\n >> Lucro total: ',cifrao,round(lucro_total,2))
                        elif resultado == 0:
                            if i == 0:
                                print('\n\nResultado: ',ativo,' EMPATE','\nValor: ',cifrao, round(resultado,2),'\n >> Lucro total: ',cifrao,round(lucro_total,2))
                            if i >=1:
                                print('\n\nResultado no gale: ',str(i),' EMPATE ',ativo,' WIN','\nLucro: ',cifrao, round(resultado,2),'\n >> Lucro total: ',cifrao,round(lucro_total,2))
                            
                            if i+1 <= martingale:
                                gale = float(entrada)
                                entrada = round(abs(gale),2)

                        else:
                            if i == 0:
                                print('\n\nResultado: ',ativo,' LOSS','\nPerca: ',cifrao, round(resultado,2),'\n >> Lucro total: ',cifrao,round(lucro_total,2))
                            if i >= 1:
                                print('\n\nResultado no gale: ',str(i),' LOSS ',ativo,'\nLucro: ',cifrao, round(resultado,2),'\n >> Lucro total: ',cifrao,round(lucro_total,2))

                            if i+1 <= martingale:
                                gale = float(entrada) * float(fator_mg)
                                entrada = round(abs(gale),2)
                        check_stop()
                        break
                if resultado > 0:
                    break
            else:
                print('Erro na abertura da ordem',id)
    if soros:
        if lucro_op_atual > 0:
            nivel_soros += 1
            lucro_op_atual = 0
        else:
            valor_soros = 0
            nivel_soros = 0
            lucro_op_atual = 0
            
def estrategia_mhi():

    global tipo


    while True:
        time.sleep(0.1)

        ###Horário do computador
        ###minutos = float(datetime.now().strftime('%M.%S')[1:])

        ###Horário da iqoption
        minutos = float(datetime.fromtimestamp(API.get_server_timestamp()).strftime('%M.%S')[1:])

        entrar = True if (minutos >= 4.59 and minutos <= 5.00) or minutos >= 9.59 else False
        print('Aguardando horário de entrada.',minutos, end = '\r')

        if (minutos >= 3.59 and minutos <= 4.00) or (minutos >= 8.59 and minutos <= 9.00):
            if tipo == 'automatico':
                binary, turbo, digital = payout(ativo)
                if digital > turbo:
                    print('\nMelhor payout: digital')
                    tipo = 'digital'
                elif turbo > digital:
                    print('\nMelhor payout: binarias')
                    tipo = 'binarias'
                else:
                    print('\nPar fechado')
                    sys.exit()
                    
        if entrar:
            print('\n >> Iniciando análise da estratégia MHI')

            direcao = False

            timeframe = 60
            qnt_velas = 7

            velas = API.get_candles(ativo,timeframe,qnt_velas,time.time())

            velas[0] = 'Verde' if velas[0]['open'] < velas[0]['close'] else 'Vermelha' if velas[0]['open'] > velas[0]['close'] else 'doji'
            velas[1] = 'Verde' if velas[1]['open'] < velas[1]['close'] else 'Vermelha' if velas[1]['open'] > velas[1]['close'] else 'doji'
            velas[2] = 'Verde' if velas[2]['open'] < velas[2]['close'] else 'Vermelha' if velas[2]['open'] > velas[2]['close'] else 'doji'
            velas[3] = 'Verde' if velas[3]['open'] < velas[3]['close'] else 'Vermelha' if velas[3]['open'] > velas[3]['close'] else 'doji'
            velas[4] = 'Verde' if velas[4]['open'] < velas[4]['close'] else 'Vermelha' if velas[4]['open'] > velas[4]['close'] else 'doji'
            velas[5] = 'Verde' if velas[5]['open'] < velas[5]['close'] else 'Vermelha' if velas[5]['open'] > velas[5]['close'] else 'doji'
            velas[6] = 'Verde' if velas[6]['open'] < velas[6]['close'] else 'Vermelha' if velas[6]['open'] > velas[6]['close'] else 'doji'

            cores = velas[0],velas[1],velas[2],velas[3],velas[4],velas[5],velas[6]

            if cores.count('Verde') > cores.count('Vermelha') and cores.count('doji') == 0: direcao = 'put'
            if cores.count('Verde') < cores.count('Vermelha') and cores.count('doji') == 0: direcao = 'call'

            if direcao:
                print('Velas: ',velas[0],velas[1],velas[2],velas[3],velas[4],velas[5],velas[6], ' - Entrada para ', direcao)
                compra(ativo,valor_entrada,direcao,1,tipo)
            else:
                print('Velas: ',velas[0],velas[1],velas[2],velas[3],velas[4],velas[5],velas[6])
                print('Entrada abortada')
            print('\n******************************************************\n')

###Inputs no inicio do robo
ativo = input('\n Digite o ativo: ').upper()
#Nexp = input('\n Informe a expedição: ')
#exp = int(Nexp)
#direcao = input('\n Digite a operação(call ou put): ')

perfil = json.loads(json.dumps(API.get_profile_ansyc()))
cifrao = str(perfil['currency_char'])
nome = str(perfil['name'])
valor_conta = float(API.get_balance())

print('\n*********************************************************************')
print('Olá, ',nome,'\nBot sendo desenvolvido por gameric.')
print('\nSeu saldo na conta',escolha,', é de: ',cifrao,valor_conta)
print('\nStop Win: ',cifrao,stop_win)
print('\nStop Loss: ',cifrao,'-',stop_loss)
print('*********************************************************************\n')

### chamada da função de compra ###
#compra(ativo,valor_entrada,direcao,exp,tipo)

### chamada da função da estrategia mhi
estrategia_mhi()

