from network import WLAN, STA_IF
from time import sleep_ms


class Rede(object):
    def __init__ (self, ssid, senha, conecta=True, txPower=None, powermode=None, reconexoes=-1, cb=None):
        self._ssid = ssid
        self._senha = senha
        self._txPower = txPower
        self._powermode = powermode
        self._reconexoes = reconexoes
        self._cb = cb
        if self._cb:
            self._cb(arg='Criando')
        self._wifi = WLAN(STA_IF)
        if conecta:
            self.conectar()


    def ativar(self):
        if self._wifi.active():
            self._wifi.active(False)
            sleep_ms(10)
        self._wifi.active(True)
        sleep_ms(100)
        if self._powermode is not None:
            self._wifi.config(pm=self._powermode)
        if self._txPower is not None:
            self._wifi.config(txpower=self._txpower)
        self._wifi.config(reconnects=self._reconexoes)


    def desativar(self):
        if self._wifi.isconnected():
            self._wifi.disconnect()
        self._wifi.active(False)


    @property
    def ativa(self):
        return self._wifi.active()


    @property
    def conectado(self):
        return self._wifi.isconnected()


    @property
    def estado(self):
        return self._wifi.status()


    def conectar(self, tentativas=10, intervalo=500):
        self.ativar()
        if self._cb:
            self._cb(arg='Iniciando conexão')

        if self._wifi.isconnected():
            self._wifi.disconnect()

        self._wifi.connect(self._ssid, self._senha)
        nt = 0
        while not self._wifi.isconnected() and nt < tentativas:
            sleep_ms(intervalo)
            nt += 1
        if self._cb:
            self._cb(arg=f'Após {nt} tentativas de conexão')
        #print (self._wifi.isconnected())
        return self._wifi.isconnected()


    def desconectar(self):
        self._wifi.disconnect()


    def configurar(self, ip, mascara, gateway, dns):
        self._wifi.ifconfig((ip, mascara, gateway, dns))


