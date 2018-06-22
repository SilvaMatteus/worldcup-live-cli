#coding: utf-8
''' World Cup Live
'''

# Available colors:
# Fore: BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE
# Back: BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, RESET.
# Style: DIM, NORMAL, BRIGHT, RESET_ALL
# TODO: Remove mocks.
# TODO: Show groups.

from multiprocessing import Process, Lock
from colorama import init, Fore, Style, Back
from time import sleep
from datetime import timedelta

import signal
import sys
import requests
import json
import dateutil.parser

NOT_RECOGNIZE = Fore.RED + 'I\'m sorry, I do not recognize this command.'
SOCCER_BALL = u"\U000026bd"
SCREEN_WIDTH = 65 # Must be odd.
UNCHECKED_BOX = u"\U00002b1c"
CHECKED_BOX = u"\U00002611"
UPDATE_TIME = 32
ASCII_ART = '' + '╦ ╦┌─┐┬─┐┬  ┌┬┐  ╔═╗┬ ┬┌─┐  ╦  ┬┬  ┬┌─┐\n' + '║║║│ │├┬┘│   ││  ║  │ │├─┘  ║  │└┐┌┘├┤ \n' + '╚╩╝└─┘┴└─┴─┘─┴┘  ╚═╝└─┘┴    ╩═╝┴ └┘ └─┘'
ASCII_ART += '0.1\nhttps://github.com/silvamatteus/worldcup-live-cli'
TIME_DIFFERENCE = -6 # In hours.

def print_help():
    print Fore.YELLOW + '%s%s%s%s%s' % (
        'Available commands: today, tomorrow, c, h.\n',
        'Live updates start when a match starts.\n',
        'Made with ', u"\U00002764", ' By @silvamatteus.\n',)

def clear_screen():
    print("\033[H\033[J")

def print_art():
    print Fore.GREEN + Style.DIM + ASCII_ART

def print_many_matches(matches, msg=None):
    if msg:
        print ' ' * (SCREEN_WIDTH/2 - len(msg)/2) + Style.DIM + Back.WHITE + Fore.CYAN + u"\U0001f4c6" + ' ' + msg
    for match in matches:
        print_match(match)

def print_match(info, is_live=False):
    if is_live:
        clear_screen()
        print_art()
        print '\n' + Fore.BLACK + Style.BRIGHT + Back.LIGHTWHITE_EX + u"\U0001f4fa" + ' LIVE ' + u"\U0001f4fa" + ' ' + Fore.YELLOW + Style.DIM + Back.RESET + ' (every ' + str(UPDATE_TIME) + ' seconds)'
    goals_home = info['home_team']['goals']
    goals_away = info['away_team']['goals']

    print Fore.BLUE + '-' * SCREEN_WIDTH,
    print
    print info['home_team']['code'],
    print Fore.GREEN + Style.BRIGHT + (SOCCER_BALL + ' ') * goals_home,
    print' ' * (SCREEN_WIDTH/2 - goals_home * 2 - 6),
    print 'x ' + ' ' * (SCREEN_WIDTH/2 - goals_away * 2 - 6),
    print Fore.GREEN + Style.BRIGHT + (SOCCER_BALL + ' ')  * goals_away,
    print info['away_team']['code']

    if info['home_team_statistics'] and info['away_team_statistics']:
        home_ball_possession = info['home_team_statistics']['ball_possession']
        away_ball_possession = info['away_team_statistics']['ball_possession']
        if home_ball_possession and away_ball_possession:
            home_ball_possession = '%02.d' % int(home_ball_possession)
            away_ball_possession = '%02.d' % int(away_ball_possession)
            print Fore.BLUE + '-' * (SCREEN_WIDTH/2 -13) + ' ' + Fore.GREEN + home_ball_possession +' - Ball Possession - ' + away_ball_possession + Fore.BLUE + ' ' + '-' * (SCREEN_WIDTH/2 -13)
    if info['status'] != 'in progress':
        print 'Match Status:' + Fore.MAGENTA + ' %s' % info['status']
    else:
        print Fore.GREEN + Style.DIM + u"\U0001f557" + ' %s' % info['time']

    if info['datetime']:
        start_time = dateutil.parser.parse(info['datetime'])
        start_time += timedelta(TIME_DIFFERENCE)
        print Fore.MAGENTA + u"\U0001f4c6" + ' %s' % start_time.strftime('%Y-%m-%d'),
        print Fore.MAGENTA + u"\U0001f557" + ' %s' % start_time.strftime('%H:%M')
    
    #TODO: print start time and current time.
    # Print goals.
    if info['status'] != 'future':
        print Fore.CYAN + ' ' * (SCREEN_WIDTH/2 -16) + '- ' + SOCCER_BALL + '  Detailed Goals Information -'
        #TODO: print details.
        goal_events_home = [event for event in info['home_team_events'] if event['type_of_event'] == 'goal' or event['type_of_event'] == 'goal-penalty']
        goal_events_away = [event for event in info['away_team_events'] if event['type_of_event'] == 'goal' or event['type_of_event'] == 'goal-penalty']
        i_events_home = 0
        i_events_away = 0
        for home_event, away_event in zip(goal_events_home, goal_events_away):
            output = home_event['player'] + ' ' + home_event['time']
            print Fore.CYAN  + output + ' ' * (SCREEN_WIDTH/2 - len(output)) + u"\U0001f557",
            output = away_event['time'] + ' ' + away_event['player']
            print Fore.CYAN + ' ' * (SCREEN_WIDTH/2 - len(output) -1) + output
            i_events_home += 1
            i_events_away += 1
        while i_events_home < len(goal_events_home):
            output = goal_events_home[i_events_home]['player'] + ' ' + goal_events_home[i_events_home]['time']
            print Fore.CYAN  + output + ' ' * (SCREEN_WIDTH/2 - len(output)) + u"\U0001f557"
            i_events_home += 1
        while i_events_away < len(goal_events_away):
            print Fore.CYAN + ' ' * (SCREEN_WIDTH/2) + u"\U0001f557",
            output = goal_events_away[i_events_away]['time'] + ' ' + goal_events_away[i_events_away]['player']
            print Fore.CYAN + ' ' * (SCREEN_WIDTH/2 - len(output) -1) + output

            i_events_away += 1


    print '\n' + ' ' * (SCREEN_WIDTH/2-1) + '···\n'

def get_live_match(lock):
    while True:
        info = []
        try:
            info = json.loads(requests.get('http://worldcup.sfg.io/matches/current').text)
            #info = json.loads('[{"venue":"Moscow","location":"Luzhniki Stadium","status":"in progress","time":"1\'","fifa_id":"300331511","home_team_statistics":{"attempts_on_goal":null,"on_target":null,"off_target":null,"blocked":null,"woodwork":null,"corners":null,"offsides":null,"ball_possession":null,"pass_accuracy":null,"num_passes":null,"passes_completed":null,"distance_covered":null,"balls_recovered":null,"tackles":null,"clearances":null,"yellow_cards":null,"red_cards":null,"fouls_committed":null,"country":"Portugal"},"away_team_statistics":{"attempts_on_goal":null,"on_target":null,"off_target":null,"blocked":null,"woodwork":null,"corners":null,"offsides":null,"ball_possession":null,"pass_accuracy":null,"num_passes":null,"passes_completed":null,"distance_covered":null,"balls_recovered":null,"tackles":null,"clearances":null,"yellow_cards":null,"red_cards":null,"fouls_committed":null,"country":"Morocco"},"datetime":"2018-06-20T12:00:00Z","last_event_update_at":"2018-06-20T12:01:04Z","last_score_update_at":"2018-06-20T12:01:19Z","home_team":{"country":"Portugal","code":"POR","goals":0},"away_team":{"country":"Morocco","code":"MAR","goals":0},"winner":null,"winner_code":null,"home_team_events":[],"away_team_events":[]}]')
        except:
            print Fore.RED + 'Ops! I can\'t connect to API =\'(' 
        if not info:
            lock.acquire()
            clear_screen()
            print_art()
            print '\n' + Fore.BLACK + Style.BRIGHT + Back.LIGHTWHITE_EX + u"\U0001f4fa" + ' No live match found.'
            lock.release()
            sleep(90)
            continue
        lock.acquire()
        print_match(info[0], is_live=True)
        lock.release()
        sleep(UPDATE_TIME)
        

def interact(lock):
    while True:
        command = raw_input()
        if command == 'today':
            todays_matches = []
            try:
                todays_matches = json.loads(requests.get('http://worldcup.sfg.io/matches/today').text)
                #todays_matches = json.loads('[{"venue":"Kazan","location":"Kazan Arena","status":"completed","time":"full-time","fifa_id":"300331496","home_team_statistics":{"attempts_on_goal":5,"on_target":0,"off_target":5,"blocked":0,"woodwork":0,"corners":2,"offsides":2,"ball_possession":30,"pass_accuracy":63,"num_passes":224,"passes_completed":142,"distance_covered":106,"balls_recovered":45,"tackles":16,"clearances":47,"yellow_cards":2,"red_cards":0,"fouls_committed":14,"country":"Iran"},"away_team_statistics":{"attempts_on_goal":17,"on_target":3,"off_target":6,"blocked":8,"woodwork":0,"corners":6,"offsides":1,"ball_possession":70,"pass_accuracy":87,"num_passes":818,"passes_completed":715,"distance_covered":104,"balls_recovered":33,"tackles":4,"clearances":11,"yellow_cards":0,"red_cards":0,"fouls_committed":14,"country":"Spain"},"datetime":"2018-06-20T18:00:00Z","last_event_update_at":"2018-06-20T19:54:18Z","last_score_update_at":"2018-06-20T19:50:29Z","home_team":{"country":"Iran","code":"IRN","goals":0},"away_team":{"country":"Spain","code":"ESP","goals":1},"winner":"Spain","winner_code":"ESP","home_team_events":[{"id":290,"type_of_event":"substitution-out","player":"Ehsan HAJI SAFI","time":"69\'"},{"id":291,"type_of_event":"substitution-in","player":"Milad MOHAMMADI","time":"69\'"},{"id":294,"type_of_event":"substitution-out","player":"Karim ANSARIFARD","time":"74\'"},{"id":295,"type_of_event":"substitution-in","player":"Alireza JAHANBAKHSH","time":"74\'"},{"id":296,"type_of_event":"yellow-card","player":"Vahid AMIRI","time":"79\'"},{"id":299,"type_of_event":"substitution-out","player":"Vahid AMIRI","time":"86\'"},{"id":300,"type_of_event":"substitution-in","player":"Saman GHODDOS","time":"86\'"}],"away_team_events":[{"id":289,"type_of_event":"goal","player":"Diego COSTA","time":"54\'"},{"id":292,"type_of_event":"substitution-out","player":"Andres INIESTA","time":"71\'"},{"id":293,"type_of_event":"substitution-in","player":"KOKE","time":"71\'"},{"id":297,"type_of_event":"substitution-out","player":"Lucas VAZQUEZ","time":"79\'"},{"id":298,"type_of_event":"substitution-in","player":"Marco ASENSIO","time":"79\'"},{"id":301,"type_of_event":"substitution-out","player":"Diego COSTA","time":"89\'"},{"id":302,"type_of_event":"substitution-in","player":"RODRIGO","time":"89\'"}]},{"venue":"Rostov-On-Don","location":"Rostov Arena","status":"completed","time":"full-time","fifa_id":"300331530","home_team_statistics":{"attempts_on_goal":13,"on_target":4,"off_target":6,"blocked":3,"woodwork":0,"corners":3,"offsides":1,"ball_possession":47,"pass_accuracy":86,"num_passes":521,"passes_completed":446,"distance_covered":100,"balls_recovered":43,"tackles":5,"clearances":18,"yellow_cards":0,"red_cards":0,"fouls_committed":10,"country":"Uruguay"},"away_team_statistics":{"attempts_on_goal":8,"on_target":3,"off_target":3,"blocked":2,"woodwork":0,"corners":4,"offsides":2,"ball_possession":53,"pass_accuracy":84,"num_passes":595,"passes_completed":499,"distance_covered":99,"balls_recovered":44,"tackles":11,"clearances":14,"yellow_cards":0,"red_cards":0,"fouls_committed":13,"country":"Saudi Arabia"},"datetime":"2018-06-20T15:00:00Z","last_event_update_at":"2018-06-20T16:53:07Z","last_score_update_at":"2018-06-20T16:52:56Z","home_team":{"country":"Uruguay","code":"URU","goals":1},"away_team":{"country":"Saudi Arabia","code":"KSA","goals":0},"winner":"Uruguay","winner_code":"URU","home_team_events":[{"id":276,"type_of_event":"goal","player":"Luis SUAREZ","time":"23\'"},{"id":279,"type_of_event":"substitution-out","player":"Cristian RODRIGUEZ","time":"59\'"},{"id":280,"type_of_event":"substitution-out","player":"Matias VECINO","time":"59\'"},{"id":281,"type_of_event":"substitution-in","player":"Lucas TORREIRA","time":"59\'"},{"id":282,"type_of_event":"substitution-in","player":"Diego LAXALT","time":"59\'"},{"id":287,"type_of_event":"substitution-out","player":"Carlos SANCHEZ","time":"82\'"},{"id":288,"type_of_event":"substitution-in","player":"Nahitan NANDEZ","time":"82\'"}],"away_team_events":[{"id":277,"type_of_event":"substitution-out","player":"TAISEER ALJASSAM","time":"44\'"},{"id":278,"type_of_event":"substitution-in","player":"HUSSAIN ALMOQAHWI","time":"44\'"},{"id":283,"type_of_event":"substitution-out","player":"HATAN BAHBRI","time":"75\'"},{"id":286,"type_of_event":"substitution-in","player":"MOHAMED KANNO","time":"75\'"},{"id":284,"type_of_event":"substitution-out","player":"FAHAD ALMUWALLAD","time":"78\'"},{"id":285,"type_of_event":"substitution-in","player":"MOHAMMED ALSAHLAWI","time":"78\'"}]},{"venue":"Moscow","location":"Luzhniki Stadium","status":"completed","time":"full-time","fifa_id":"300331511","home_team_statistics":{"attempts_on_goal":10,"on_target":2,"off_target":4,"blocked":4,"woodwork":0,"corners":5,"offsides":1,"ball_possession":46,"pass_accuracy":70,"num_passes":388,"passes_completed":273,"distance_covered":105,"balls_recovered":47,"tackles":12,"clearances":39,"yellow_cards":1,"red_cards":0,"fouls_committed":19,"country":"Portugal"},"away_team_statistics":{"attempts_on_goal":16,"on_target":4,"off_target":10,"blocked":2,"woodwork":0,"corners":7,"offsides":1,"ball_possession":54,"pass_accuracy":75,"num_passes":470,"passes_completed":352,"distance_covered":107,"balls_recovered":65,"tackles":16,"clearances":16,"yellow_cards":1,"red_cards":0,"fouls_committed":23,"country":"Morocco"},"datetime":"2018-06-20T12:00:00Z","last_event_update_at":"2018-06-20T13:55:37Z","last_score_update_at":"2018-06-20T13:55:28Z","home_team":{"country":"Portugal","code":"POR","goals":1},"away_team":{"country":"Morocco","code":"MAR","goals":0},"winner":"Portugal","winner_code":"POR","home_team_events":[{"id":259,"type_of_event":"goal","player":"CRISTIANO RONALDO","time":"4\'"},{"id":261,"type_of_event":"substitution-out","player":"BERNARDO SILVA","time":"59\'"},{"id":262,"type_of_event":"substitution-in","player":"GELSON MARTINS","time":"59\'"},{"id":265,"type_of_event":"substitution-out","player":"JOAO MARIO","time":"70\'"},{"id":266,"type_of_event":"substitution-in","player":"BRUNO FERNANDES","time":"70\'"},{"id":273,"type_of_event":"substitution-out","player":"JOAO MOUTINHO","time":"89\'"},{"id":274,"type_of_event":"substitution-in","player":"ADRIEN SILVA","time":"89\'"},{"id":275,"type_of_event":"yellow-card","player":"ADRIEN SILVA","time":"90\'+2\'"}],"away_team_events":[{"id":260,"type_of_event":"yellow-card","player":"Mehdi BENATIA","time":"40\'"},{"id":263,"type_of_event":"substitution-out","player":"Khalid BOUTAIB","time":"69\'"},{"id":264,"type_of_event":"substitution-in","player":"Ayoub EL KAABI","time":"69\'"},{"id":268,"type_of_event":"substitution-out","player":"Khalid BOUTAIB","time":"70\'"},{"id":269,"type_of_event":"substitution-in","player":"AyoubEL KAABI","time":"70\'"},{"id":267,"type_of_event":"substitution-out","player":"Younes BELHANDA","time":"75\'"},{"id":270,"type_of_event":"substitution-in","player":"Mehdi CARCELA","time":"75\'"},{"id":271,"type_of_event":"substitution-out","player":"Karim EL AHMADI","time":"86\'"},{"id":272,"type_of_event":"substitution-in","player":"Faycal FAJR","time":"86\'"}]}]')
            except:
                print Fore.RED + 'Ops! I can\'t connect to API =\'('

            lock.acquire()
            print_many_matches(todays_matches, msg='Today\'s Matches:')
            lock.release()
        elif command == 'tomorrow':
            tomorrow_matches = []
            try:
                tomorrow_matches = json.loads(requests.get('http://worldcup.sfg.io/matches/tomorrow').text)
            except:
                print Fore.RED + 'Ops! I can\'t connect to API =\'('

            lock.acquire()
            print_many_matches(tomorrow_matches, msg='Tomorrow\'s Matches:')
            lock.release()
        elif command == 'c':
            clear_screen()
            print_art()
        elif command == 'h' or command == 'help':
            print_help()
        else:
            lock.acquire()
            print NOT_RECOGNIZE
            print_help()
            lock.release()

def sigterm_handler(signal, frame):
    # save the state here or do whatever you want
    sys.exit(0)


if __name__ == '__main__':
    # Setup signal handlers.
    signal.signal(signal.SIGINT, sigterm_handler)
    signal.signal(signal.SIGTERM, sigterm_handler)

    # Lock for prints
    lock = Lock()

    # Init colorama
    init(autoreset=True)
    clear_screen()
    print_art()
    Process(target=get_live_match, args=([lock])).start()
    interact(lock)
