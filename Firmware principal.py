from machine import Pin, ADC, reset, Timer
from time import sleep_ms, time, ticks_ms, ticks_diff
from ntptime import settime
from dht import DHT11
from onewire import OneWire
from ds18x20 import DS18X20
from hx711 import HX711
from rede import Rede
from umqtt.robust import MQTTClient
from json import dumps, load

Soil = ADC(Pin(34))
Soil.atten(ADC.ATTN_11DB)
DHT = DHT11(Pin(21, Pin.IN))
DS = DS18X20(OneWire(Pin(27)))
hx = HX711(dout=Pin(26), pd_sck=Pin(25), gain=128)
valvula = Pin(12, Pin.OUT)
confirma = Pin(2, Pin.OUT)

with open('config.json', 'r') as arq:
    cfg = load(arq)

def debug (arg):
    print(arg)

def cbTimer(t):
    global taNaHora
   
    taNaHora = True

r = Rede(cfg['rede'], cfg['senha'], cb=debug)
r.conectar(tentativas = 40, intervalo = 1000)

topTelemetria = b"v1/devices/me/telemetry"

if r.conectado:
    confirma.on()
    try:
        settime()
        cliente = MQTTClient(cfg["clientId"], cfg["broker"], user=cfg["userbroker"], password='')
        cliente.connect()
    except:
        print ('Não foi possivel conectar a rede... Tentando novamente.')
        sleep_ms(2000)
        reset()

def umidade_solo(x):
    leitura = x.read()
    if leitura > 3100:
        leitura = 3100
    elif leitura < 1900:
        leitura = 1900
    umidade = int((3100 - leitura) * 100 / (3100 - 1900))
    return umidade

def temp_umid_amb (x):
    x.measure()
    temp = x.temperature()
    umid = x.humidity()
    return temp, umid

def temp_solo (x):
    roms = x.scan()
    x.convert_temp()
    t = ticks_ms()
    while ticks_diff(ticks_ms(), t) < 750:
        pass
    for rom in roms:
        temp = x.read_temp(rom)
    return temp

def peso (x):
    m = x.read_average(10)
    peso = (((-0.00213) * m) - 448) - 25
    return peso

taNaHora = False
timm = Timer(0)
timm.init(mode = Timer.PERIODIC,
          period = 2000,
          callback = cbTimer)

dados = {'ts': 0, 'values':{}}
irriga = {'ts': 0, 'values':{}}
confirma.off()

estado_irrigacao = 0
inicio_etapa = 0
peso_ant = 0

while True:
    if r.conectado and taNaHora:    
        dados['ts'] = (time()+946684800)*1000
        dados['values']['umid_solo'] = (umidade_solo(Soil))
        dados['values']['temp_solo'] = (temp_solo(DS))
        temp_amb, umid_amb = temp_umid_amb(DHT)
        dados['values']['temp_ambiente'] = (temp_amb)
        dados['values']['umid_ambiente'] = (umid_amb)
        payload = (dumps(dados).encode())
        cliente.publish(topTelemetria, payload)
        taNaHora = False   
       
    umid = umidade_solo(Soil)

    if estado_irrigacao == 0:
        if umid <= 30:
            estado_irrigacao = 1
            inicio_etapa = ticks_ms()
            peso_ant = peso(hx)
            valvula.on()

    elif estado_irrigacao == 1:
        if ticks_diff(ticks_ms(), inicio_etapa) >= 10000:
            valvula.off()
            estado_irrigacao = 2
            inicio_etapa = ticks_ms()

    elif estado_irrigacao == 2:
        if ticks_diff(ticks_ms(), inicio_etapa) >= 3000:
            if umidade_solo(Soil) >= 70:
                agua = (peso(hx)) - peso_ant
                irriga['ts'] = (time()+946684800)*1000
                irriga['values']['irrigacao'] = agua
                cliente.publish(topTelemetria, dumps(irriga))
                estado_irrigacao = 0
            else:
                estado_irrigacao = 1
                inicio_etapa = ticks_ms()
                valvula.on()

