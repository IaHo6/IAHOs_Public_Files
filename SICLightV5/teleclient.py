import socket
import errno
import sys
import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
import re
from datetime import datetime



HEADER_LENGTH = 10
IP = "127.0.0.1"
PORT = 1236

sun_start_time_str = '07:00:00'
sun_pause_time_str = '22:00:00'
sun_start_time = datetime.strptime(sun_start_time_str, '%H:%M:%S').time()
sun_pause_time = datetime.strptime(sun_pause_time_str, '%H:%M:%S').time()

telemessage = None
customcolor = False
morsecode = False
sunpauseedit = False
sunpausestart = False
sunpausestop = False
color_dict = {}



def colorcustom(input_str, chat_id):
    global color_dict
    # Regular expression, um den Namen und den RGB-Code zu extrahieren
    pattern = r'([a-z]+)(\d{1,3})/(\d{1,3})/(\d{1,3})'
    
    # Sucht nach dem Muster im Eingabestring
    match = re.match(pattern, input_str)
    
    if match:
        # Extrahiert den Namen und die RGB-Werte
        name = match.group(1)
        # Extrahiere die RGB-Werte als Ganzzahlen
        rgb_values = [int(match.group(i)) for i in range(2, 5)]
        
        # Überprüfe, ob die RGB-Werte im Bereich von 0 bis 255 liegen
        if all(0 <= value <= 255 for value in rgb_values):
            # Erstellt das Dictionary
            color_dict[name] = rgb_values
            return name
        else:
            telegram_bot.sendMessage (chat_id, 'Die RGB werte müssen zwischen 0 und 255 liegen.')
            telegram_bot.sendMessage (chat_id, 'Versuchen Sie es nochmals.',
                                      reply_markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Abbrechen",callback_data='q')]]))
            raise ValueError("RGB-Werte müssen zwischen 0 und 255 liegen.")
    else:
        telegram_bot.sendMessage (chat_id, 'Ungültiges Format')
        telegram_bot.sendMessage (chat_id, 'Versuchen Sie es nochmals.',
                                  reply_markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Abbrechen",callback_data='q')]]))
        raise ValueError("Ungültiges Format.")
    

def is_valid_time(time_string):
    try:
        time_obj = datetime.strptime(time_string, "%H:%M:%S").time()
        return time_obj
    except ValueError:
        return False
    

def action(msg):
    global telemessage
    global customcolor
    global morsecode
    global sunpauseedit
    global sunpausestart
    global sunpausestop
    global sun_pause_time
    global sun_start_time

    flavour = telepot.flavor(msg)
    if flavour == 'chat':
        chat_id = msg['chat']['id']
        command = msg['text']
    else:
        chat_id = msg['from']['id']
        command = msg['data']
    print('Received: %s' % command)
    if sunpausestart:
        x = is_valid_time(command)
        if x:
            sun_start_time = x
            telegram_bot.sendMessage (chat_id, f'Sie haben die Startzeit der Sonne erfolgreich auf {x} geändert.')
            command = "*s" + str(x)
            sunpauseedit = False
            sunpausestart = False
            sunpausestop = False
        else:
            telegram_bot.sendMessage (chat_id, f'Ungültige Eingabe.')
    if sunpausestop:
        x = is_valid_time(command)
        if x:
            sun_pause_time = x
            telegram_bot.sendMessage (chat_id, f'Sie haben die Stopzeit der Sonne erfolgreich auf {x} geändert.')
            command = "*p" + str(x)
            sunpauseedit = False
            sunpausestart = False
            sunpausestop = False
        else:
            telegram_bot.sendMessage (chat_id, f'Ungültige Eingabe.')
    if sunpauseedit:
        if command == "/start":
            telegram_bot.sendMessage (chat_id, f'Geben Sie die Zeit ein, bei der die Sonne eingeschalten werden soll.', reply_markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Abbrechen",callback_data="/qsunpause")]]))
            sunpausestart = True
        elif command == "/pause":
            sunpausestop = True
            telegram_bot.sendMessage (chat_id, f'Geben Sie die Zeit ein, bei der die Sonne ausgeschalten werden soll.', reply_markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Abbrechen",callback_data="/qsunpause")]]))
        elif command == "/qsunpause":
            telegram_bot.sendMessage (chat_id, f'Sie haben die Einstellungen abgebrochen.')
            sunpauseedit = False
            sunpausestart = False
            sunpausestop = False
        else:
            telegram_bot.sendMessage (chat_id, f'Ungültige Eingabe.')
    elif customcolor:
        if command == "q":
            telegram_bot.sendMessage (chat_id, 'Sie haben das Erstellen einer eigenen Farbe abgebrochen.')
            customcolor = False
        else:
            try:
                result = colorcustom(command.lower(), chat_id)
                print(result)
                print(color_dict)
                telegram_bot.sendMessage (chat_id, f'Sie haben erfolgreich eine neue Farbe erstellt: {str(color_dict[result])[1:-1]}\nSie können diese mit dem Befehl /{result} abrufen.')
                customcolor = False
            except ValueError as e:
                print(e)
    elif morsecode:
        if command == "q":
            telegram_bot.sendMessage (chat_id, 'Sie haben das Morsen abgebrochen.')
            morsecode = False
        else:
            morsecode = False
            telegram_bot.sendMessage(chat_id, "Der MorseCode von Ihrem Text wird jetzt mit dem Licht sichtbar gemacht. Schau genau hin und Blinzel nicht.")
    elif command == '/hi' or command == '/start':
        telegram_bot.sendMessage (chat_id, "Hallo, Willkommen beim Raspberry-Pi Kontrollzentrum um das Licht zu steuern. Viel Spass!",
                                  reply_markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Liste aller Befehle",callback_data='/hilfe')]]))
    
    elif command == '/hilfe':
        colors = []
        for color in color_dict.keys():
            colors.append(InlineKeyboardButton(text=f'{color.title()}: {str(color_dict[color])[1:-1]}',callback_data=f'/{color}'))
        buttons = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Willkommens-Nachricht",callback_data='/start')],
            [InlineKeyboardButton(text="Liste aller Befehle",callback_data='/hilfe')],
            [InlineKeyboardButton(text="Lichter Aus",callback_data='/stop')],
            [InlineKeyboardButton(text="Sonne",callback_data='/sun')],
            [InlineKeyboardButton(text="Sonne Verschieben",callback_data='/sunshift')],
            [InlineKeyboardButton(text="Sonnenpause ändern",callback_data='/sunpause')],
            [InlineKeyboardButton(text="Weiss",callback_data='/weiss'),
             InlineKeyboardButton(text="Rot",callback_data='/rot'),
             InlineKeyboardButton(text="Orange",callback_data='/orange'),
             InlineKeyboardButton(text="Gelb",callback_data='/gelb'),],
            [InlineKeyboardButton(text="Grün",callback_data='/gruen'),
             InlineKeyboardButton(text="Türkis",callback_data='/tuerkis'),
             InlineKeyboardButton(text="Blau",callback_data='/blau'),
             InlineKeyboardButton(text="Violet",callback_data='/violet'),],
            [InlineKeyboardButton(text="Regenbogen Animation",callback_data='/regenbogen')],
            [InlineKeyboardButton(text="Zweite Regenbogen Animation",callback_data='/regenbogen2')],
            [InlineKeyboardButton(text="Regenbogen Kreis",callback_data='/regenbogenkreis')],
            [InlineKeyboardButton(text="Nerd Modus",callback_data='/nerd')],
            [InlineKeyboardButton(text="Morsen",callback_data='/morsecode')],
            [InlineKeyboardButton(text="eigene Farbe erstellen",callback_data='/eigenefarbe')],
            colors,
            [InlineKeyboardButton(text="Herunterfahren",callback_data='/tryshutdown')],
            ])
        telegram_bot.sendMessage (chat_id, "Hier ist eine übersicht von allen Befehlen.", reply_markup=buttons)
    elif command == '/quit':
        telegram_bot.sendMessage(chat_id, "ACHTUNG! Sie haben das Programm abgeschalten. Solange der Raspberry Pi neu gestartet wurde, wird der Bot nicht funktionieren.")
    elif command == '/tryshutdown':
        telegram_bot.sendMessage(chat_id, "Sind Sie sicher das sie den Raspberry Pi herunterfahren wollen?",
                                 reply_markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Herunterfahren",callback_data='/shutdown')],
                                                                                      [InlineKeyboardButton(text="Abbrechen",callback_data='/stopshutdown')]]))
    elif command == '/shutdown':
        telegram_bot.sendMessage(chat_id, 'ACHTUNG! Sie haben den Raspberry Pi heruntergefahren. Sie müssen ihn neustarten, bevor Sie wieder Befehle geben können.')
    elif command == '/stopshutdown':
        telegram_bot.sendMessage(chat_id, 'Gute Wahl. Jetzt können sie länger das Licht geniessen.')
    elif command == '/morsecode':
        morsecode = True
        telegram_bot.sendMessage(chat_id, 'Bitte geben Sie den Text ein den sie als Morse Code anzeigen lassen wollen (Beispiel: RaspberryPi isch es cools Möbel)',
                                      reply_markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Abbrechen",callback_data='q')]]))
    elif command == '/regenbogen':
        telegram_bot.sendMessage(chat_id, 'Regenbogen Modus ist aktiv')
    elif command == '/sun':
        telegram_bot.sendMessage(chat_id, 'Sonnen Modus ist aktiv')
    elif command == '/sunshift':
        telegram_bot.sendMessage(chat_id, 'Verschiebe die Sonne nach vorne oder nach hinten',
                                 reply_markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="-",callback_data='shiftminus'),
                                                                                       InlineKeyboardButton(text="+",callback_data='shiftplus')]]))
    elif command == '/regenbogenkreis':
        telegram_bot.sendMessage(chat_id, 'Regenbogen Kreis ist aktiv')  
    elif command == '/regenbogen2':
        telegram_bot.sendMessage(chat_id, 'Regenbogen2 Modus ist aktiv') 
    elif command == '/nerd':
        telegram_bot.sendMessage(chat_id, 'Nerd Modus ist aktiv\nnur Nerds werden Verstehen')
    elif command == '/stop':
        telegram_bot.sendMessage(chat_id, 'Die Lichter werden ausgeschalten')
    elif command == '/weiss':
        telegram_bot.sendMessage(chat_id, 'Die Lichter werden Weiss')
    elif command == '/rot':
        telegram_bot.sendMessage(chat_id, 'Die Lichter werden Rot')
    elif command == '/orange':
        telegram_bot.sendMessage(chat_id, 'Die Lichter werden Orange')
    elif command == '/gelb':
        telegram_bot.sendMessage(chat_id, 'Die Lichter werden Gelb')
    elif command == '/gruen':
        telegram_bot.sendMessage(chat_id, 'Die Lichter werden Grün')
    elif command == '/tuerkis':
        telegram_bot.sendMessage(chat_id, 'Die Lichter werden Türkis')
    elif command == '/blau':
        telegram_bot.sendMessage(chat_id, 'Die Lichter werden Blau')
    elif command == '/violet':
        telegram_bot.sendMessage(chat_id, 'Die Lichter werden Violet')
    elif command == '/eigenefarbe':
        telegram_bot.sendMessage(chat_id, 'Bitte geben Sie die RGB Werte ein und den zugehörigen Namen, im folgendem Format:\n"nameRRR/GGG/BBB"',
                                 reply_markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Abbrechen",callback_data='q')]]))
        customcolor = True
    elif command == '/sunpause':
        telegram_bot.sendMessage(chat_id, 'Möchten sie die Morgen/Start - Zeit oder die Abend/Stop - Zeit ändern?',
                                 reply_markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Morgen/Start - Zeit", callback_data="/start"), 
                                                                                       InlineKeyboardButton(text="Abend/Stop - Zeit", callback_data="/pause")],
                                                                                      [InlineKeyboardButton(text="Abbrechen",callback_data="/qsunpause")]]))
        sunpauseedit = True
    elif command.startswith('/'):
                if command[1:] in color_dict.keys():
                    print(command)
                    telegram_bot.sendMessage(chat_id, f'Die Lichter sind jetzt: RGB({str(color_dict[command[1:]])[1:-1]})')
    
    telemessage = command
    if flavour == 'callback_query':
        telegram_bot.answerCallbackQuery(msg['id'], command)
        
telegram_bot = telepot.Bot('6316661559:AAFLw-T7CzyDAmWkNu4gbfi3Pa-yfOb0Oy0')
print(telegram_bot.getMe())

MessageLoop(telegram_bot, action).run_as_thread()
print('Up and Running....')

my_username = "TeleClient"
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((IP, PORT))
client_socket.setblocking(False)

username = my_username.encode('utf-8')
username_header = f"{len(username):<{HEADER_LENGTH}}".encode('utf-8')
client_socket.send(username_header + username)

while True:
    message = telemessage
    if message:
        message = message.encode('utf-8')
        message_header = f"{len(message):<{HEADER_LENGTH}}".encode('utf-8')
        client_socket.send(message_header + message)
    telemessage = None

    try:
            while True:
                #receive things
                username_header = client_socket.recv(HEADER_LENGTH)
                if not len(username_header):
                    print("Connection closed by the server")
                    sys.exit()
                username_length = int(username_header.decode('utf-8').strip())
                username = client_socket.recv(username_length).decode('utf-8')

                message_header = client_socket.recv(HEADER_LENGTH)
                message_length = int(message_header.decode('utf-8').strip())
                message = client_socket.recv(message_length).decode('utf-8')
                

                print(f"{username} > {message}")
        

    except IOError as e:
        if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
              print('Reading error',str(e))
              sys.exit()
        continue

    except Exception as e:
        print('General error', str(e))
        sys.exit()
