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

### Função abrir ordem e checar resultado ###
def compra(ativo,valor_entrada,direcao,exp,tipo):
    if tipo == 'digital':
        check, id = API.buy_digital_spot_v2(ativo,valor_entrada,direcao,exp)
    else:
        check, id = API.buy(valor_entrada,ativo,direcao,exp)

    if check:
        print('\nOrdem Aberta',id, '\n >>Ativo: ',ativo,'\n >>Valor: ',cifrao,valor_entrada,'\n >>tempo: ',exp,'min')

        while True:
            time.sleep(0.1)
            status, resultado = API.check_win_digital_v2(id) if tipo == 'digital' else API.check_win_v4(id)

            if status:
                if resultado > 0:
                    print('\n\nResultado: ',ativo,' WIN','\nLucro: ',cifrao, round(resultado,2),)
                elif resultado == 0:
                    print('\n\nResultado: ',ativo,' EMPATE','\nValor: ',cifrao, round(resultado,2))
                else:
                    print('\n\nResultado: ',ativo,' LOSS','\nPerca: ',cifrao, round(resultado,2))
                break
    else:
        print('Erro na abertura da ordem',id)

def estrategia_mhi():
    while True:
        time.sleep(0.1)

        ###Horário do computador
        ###minutos = float(datetime.now().strftime('%M.%S')[1:])

        ###Horário da iqoption
        minutos = float(datetime.fromtimestamp(API.get_server_timestamp()).strftime('%M.%S')[1:])

        entrar = True if (minutos >= 4.59 and minutos <= 5.00) or minutos >= 9.59 else False
        print('Aguardando horário de entrada.',minutos, end = '\r')

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
print('*********************************************************************\n')

### chamada da função de compra ###
#compra(ativo,valor_entrada,direcao,exp,tipo)

### chamada da função da estrategia mhi
estrategia_mhi()

