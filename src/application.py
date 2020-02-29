import subprocess
from aiohttp import web

from aioalice import Dispatcher, get_new_configured_app
from aioalice.dispatcher import MemoryStorage

from states import UserStates, DosStates, PingStates


WEBHOOK_URL_PATH = '/my-alice-webhook/'

WEBAPP_PORT = 8080


dp = Dispatcher(storage=MemoryStorage())


@dp.request_handler(func=lambda areq: areq.session.new)
async def handle_new_session(alice_request):
    user_id = alice_request.session.user_id
    await dp.storage.set_state(user_id, UserStates.SELECT_COMMAND)
    return alice_request.response('Привет! Что будем делать ?',
                                  buttons=['Атаковать',
                                           'Пинг'])


@dp.request_handler(state=UserStates.SELECT_COMMAND,
                    commands=['атаковать', 'атака'])
async def handle_select_host_attack(alice_request):
    user_id = alice_request.session.user_id
    await dp.storage.update_data(user_id=user_id,
                                 data={'dos': None})
    await dp.storage.set_state(user_id, DosStates.SELECT_HOST_DOS)
    return alice_request.response('Какой хост атакуем ?')


@dp.request_handler(state=DosStates.SELECT_HOST_DOS)
async def handle_start_attack(alice_request):
    user_id = alice_request.session.user_id
    request_text = alice_request.request.original_utterance
    proc = subprocess.Popen(
        ['python', './src/slowloris.py', request_text]
    )
    await dp.storage.update_data(user_id=user_id,
                                 data={'dos': proc})
    await dp.storage.set_state(user_id, DosStates.START_ATTACK)
    print(proc.pid)
    return alice_request.response('Пакетики полетели')


@dp.request_handler(state=DosStates.START_ATTACK,
                    commands=['стоп', 'хватит', 'прекрати',
                              'остановись', 'нельзя', 'фу'])
async def handle_stop_attack(alice_request):
    user_id = alice_request.session.user_id
    data = await dp.storage.get_data(user_id)
    proc = data['dos']
    proc.terminate()
    await dp.storage.set_state(user_id, UserStates.SELECT_COMMAND)
    return alice_request.response('Остановочка. Что дальше ?',
                                  buttons=['Атаковать',
                                           'Пинг'])


@dp.request_handler(state=UserStates.SELECT_COMMAND,
                    commands=['пинг', 'ping'])
async def handle_select_host_ping(alice_request):
    user_id = alice_request.session.user_id
    await dp.storage.set_state(user_id, PingStates.SELECT_HOST_PING)
    return alice_request.response('Какой хост пингуем ?')


@dp.request_handler(state=PingStates.SELECT_HOST_PING)
async def handle_start_ping(alice_request):
    user_id = alice_request.session.user_id
    request_text = alice_request.request.original_utterance
    result = subprocess.call(['ping', '-c', '1', request_text])
    await dp.storage.set_state(user_id, UserStates.SELECT_COMMAND)
    if result == 0:
        return alice_request.response('Пакетики доставлены. Что дальше ?',
                                      buttons=['Атаковать',
                                               'Пинг'])
    else:
        return alice_request.response('Пакетики не доставлены. Что дальше ?',
                                      buttons=['Атаковать',
                                               'Пинг'])


@dp.request_handler()
async def handle_other_commands(alice_request):
    return alice_request.response('Читай доки',
                                  buttons=['Атаковать',
                                           'Пинг'])


if __name__ == '__main__':
    app = get_new_configured_app(dispatcher=dp, path=WEBHOOK_URL_PATH)
    web.run_app(app, host='127.0.0.1', port=WEBAPP_PORT)
