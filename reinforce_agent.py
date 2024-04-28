from IPython.display import clear_output
import time, random, copy
import numpy as np

# Die Umgebung
class Umgebung(object):
    def __init__(self,width,height):
        self.width = width
        self.height = height
        self.R = {} # Reward
        self.environment = {}
        self.scene = {}
        self.init_environment()
        self.init_R()


    def init_R(self):
        for _, right in enumerate([Const.WAND,Const.BESUCHT,Const.UNBESUCHT]):
            for _, down in enumerate([Const.WAND,Const.BESUCHT,Const.UNBESUCHT]):
                for _, left in enumerate([Const.WAND,Const.BESUCHT,Const.UNBESUCHT]):
                    for _, up in enumerate([Const.WAND,Const.BESUCHT,Const.UNBESUCHT]):
                        #Dictionary für die Werte, um einfach darauf zuzugreifen
                        self.R[right,down,left,up] = \
                            {Const.RECHTS:self.R_val(right),Const.UNTEN:self.R_val(down),Const.LINKS:self.R_val(left),Const.OBEN:self.R_val(up)}    

    def R_val(self,cell_val):
        if cell_val == Const.WAND:
            return -10.0 
        elif cell_val == Const.UNBESUCHT:
            return +5.0 
        elif cell_val == Const.BESUCHT:
            return -3.0
        else: 
            return 0.0 


# Der Agent                      
class Agent(object):
    def __init__(self,posx,posy,umgebung,gamma=0.8,alpha=1.0,epsilon=0.2):
        self.init_agent(posx,posy,gamma,alpha,epsilon)
        self.umgebung = umgebung
        self.sensor_werte = {}
        self.reaktion = {} #Code und Text, Code = 0=OK/1=Wand/2=Kollege
        self.Q = {}
        self.init_Q()

    def init_agent(self,posx=-1,posy=-1,gamma=0.8,alpha=1.0,epsilon=0.2):
        self.moves = 0     # Wie oft habe ich mich bewegt, der erste Move ist das Platzieren beim Start
        self.moves_2_u = 1 # Wie viele unbesuchte habe ich besucht, der erste ist immer unbesucht
        self.moves_2_b = 0
        self.moves_2_w = 0
        self.score = 0
        self.gamma = gamma
        self.alpha = alpha # Lernrate
        self.epsilon = epsilon # Grenze für zufällige Selektion der Aktion
        if posx == -1 and posy == -1:
            self.random_pos()
        else:
            self.set_pos(posx,posy)
        
    def init_Q(self):
        for _, right in enumerate([Const.WAND,Const.BESUCHT,Const.UNBESUCHT]):
            for _, down in enumerate([Const.WAND,Const.BESUCHT,Const.UNBESUCHT]):
                for _, left in enumerate([Const.WAND,Const.BESUCHT,Const.UNBESUCHT]):
                    for _, up in enumerate([Const.WAND,Const.BESUCHT,Const.UNBESUCHT]):
                        q_right = 0.1
                        q_down = 0.2
                        q_left = 0.3
                        q_up = 0.4
                        #Dictionary für die Werte, um einfach darauf zuzugreifen
                        q_val = {Const.RECHTS:q_right,Const.UNTEN:q_down,Const.LINKS:q_left,Const.OBEN:q_up}
                        self.Q[right,down,left,up] = q_val

    def move_me_q(self):
        self.moves += 1
        posx_neu = self.posx
        posy_neu = self.posy

        action = self.get_max_q_action()
        # print("action: {} {}".format(action, print_flag))

        if action == Const.LINKS:
            posx_neu -= 1
        elif action == Const.RECHTS:
            posx_neu += 1
        elif action == Const.OBEN:
            posy_neu -= 1
        elif action == Const.UNTEN:
            posy_neu += 1

        # Wand oder Kollege
        if self.sensor_werte[action] != Const.WAND:            
            self.posx = posx_neu
            self.posy = posy_neu  
        
        # Moves 2 Unbesucht
        if self.umgebung.environment[self.posx,self.posy] == Const.UNBESUCHT:
            self.moves_2_u += 1
        # Moves 2 Besucht
        if self.umgebung.environment[self.posx,self.posy] == Const.BESUCHT:
            self.moves_2_b += 1 
        # Moves 2 Wand
        if self.sensor_werte[action] == Const.WAND:
            self.moves_2_w += 1             
      
    def get_max_q_action_key(self,q_values):
        action_keys = []
    
        action = max(q_values, key=lambda k: q_values[k])
        for key, value in q_values.items():
            if value == q_values[action]:
                action_keys.append(key)
        #print("Action Keys: {}".format(action_keys))
        action = random.choice(action_keys)
        return action, action_keys
    
    def get_max_q_action(self):
        action_keys = []
        sensor = self.sensieren()
        state = (sensor[Const.RECHTS],sensor[Const.UNTEN],sensor[Const.LINKS],sensor[Const.OBEN])
        q_values = self.Q.get(state)
        #print("q_values: {}".format(q_values))
        action = max(q_values, key=lambda k: q_values[k])
        for key, value in q_values.items():
            if value == q_values[action]:
                action_keys.append(key)
        #print("Action Keys: {}".format(action_keys))
        action = random.choice(action_keys)
        return action
        
    def next_state(self,actual_state,action):
        posx_neu = self.posx
        posy_neu = self.posy

        if action == Const.LINKS:
            posx_neu -= 1
        elif action == Const.RECHTS:
            posx_neu += 1
        elif action == Const.OBEN:
            posy_neu -= 1
        elif action == Const.UNTEN:
            posy_neu += 1

        # Wand oder Kollege
        if self.sensor_werte[action] == Const.WAND:            
            return self.sensieren()
        else:
            return self.sensieren(posx_neu,posy_neu)       
        
    def action(self,print_flag=False,alpha=1.0):
        self.moves += 1
        status = ''
        self.alpha = alpha # Lernrate
         # Aktueller Zustand: Die Umgebunginformation einholen
        actual_posx = self.posx
        actual_posy = self.posy
        sensor = self.sensieren()
        actual_state = (sensor[Const.RECHTS],sensor[Const.UNTEN],sensor[Const.LINKS],sensor[Const.OBEN])
        # 3.2.1 Nächster Schritt - zufällig
        action, selection_style = self.choose_action(print_flag)
        # 3.2.2 Ermittelter nächster Zustand
        sensor = self.next_state(actual_state,action)
        next_state = (sensor[Const.RECHTS],sensor[Const.UNTEN],sensor[Const.LINKS],sensor[Const.OBEN])
        # 3.2.3 Ermittle den maximalen Q-Wert für alle möglichen Aktionen im nächsten Zustand
        next_q_values = self.Q.get(next_state).values() 
        max_q = max(self.Q.get(next_state).values())
        # 3.2.4 Berechne den neuen Q-Wert mit Hilfe der Bellman Gleichung
        q_neu = ( 1.0 - self.alpha ) * self.Q.get(actual_state)[action] + \
                self.alpha * ( self.umgebung.R.get(actual_state)[action] + \
                self.gamma * max_q )
            
        old_q_values = copy.deepcopy(self.Q.get(actual_state)).values()
        old_q = copy.deepcopy(self.Q.get(actual_state))
        old_q_value = self.Q[actual_state][action]
        self.Q[actual_state][action] = round(q_neu,4)
        new_q_values = copy.deepcopy(self.Q.get(actual_state)).values()
        new_q = copy.deepcopy(self.Q.get(actual_state))
        # Gab es eine Änderung bei den maximal Werten
        max_action_old, max_action_keys_old = self.get_max_q_action_key(old_q)
        max_action_new, max_action_keys_new = self.get_max_q_action_key(new_q)
        
        if (max_action_old != max_action_new) and ( print_flag == True):
            print("{} Q: {} Old Q: {} New Q: {}".format(selection_style, actual_state,old_q_values,new_q_values))
        
        # 3.2.5 Setze den nächsten Zustand als den aktuellen Zustand      
        self.move_me(action) 
        new_posx = self.posx
        new_posy = self.posy        
        # Gesamtbelohnung 
        self.score += self.umgebung.R.get(actual_state)[action] 
        # Moves 2 Unbesucht
        if self.umgebung.environment[new_posx,new_posy] == Const.UNBESUCHT:
            self.moves_2_u += 1
        
        if print_flag == True:
            print("Moves: {}".format(self.moves))
            print("Moves2U: {} {}".format(self.moves_2_u, self.umgebung.environment[actual_posx,actual_posy]))
            print("Score: {}".format(self.score))
            print("Aktuelle Position: {} {}".format(actual_posx,actual_posy))
            print("Aktueller Zustand: {}".format(actual_state))
            print("Aktion: {}".format(action))
            print("Nächster Zustand: {}".format(next_state))
            print("Belohnung: {}".format(self.umgebung.R.get(actual_state)[action]))
            print("Q alt: {} {}".format(old_q_value,old_q_values))
            print("Max Q: {} {}".format(max_q,next_q_values))
            print("Alpha: {} Gamma: {}".format(self.alpha,self.gamma))
            print("Q neu: {}".format(q_neu))           
            print("Q Eintrag neu: {} {}".format(q_neu,new_q_values))          
            print("Neue Position: {} {}".format(new_posx,new_posy))
            print("----------------------------------------------------")

        return actual_state
    
    def choose_action(self,print_flag=False):
        selection_style = ''
        random_val = random.uniform(0,1)
        if print_flag == True:
            print("Random Val: {} Epsilon: {}".format(random_val,self.epsilon))
        if random_val >= self.epsilon:
            next_action = random.choice([Const.RECHTS,Const.UNTEN,Const.LINKS,Const.OBEN])
            selection_style = 'RANDOM'
            if print_flag == True:
                print("Random {}".format(next_action))
        else:
            next_action = self.get_max_q_action()
            selection_style = 'MAX'
            if print_flag == True:
                print("Max Q {}".format(next_action))
        return next_action, selection_style      
            
    def sensieren(self,posx=-1,posy=-1):
        sensor_werte = {}
        if posx == -1 and posy == -1:
            self.sensor_werte[Const.RECHTS] = self.umgebung.environment[self.posx+1,self.posy] 
            self.sensor_werte[Const.UNTEN] = self.umgebung.environment[self.posx,self.posy+1] 
            self.sensor_werte[Const.OBEN] = self.umgebung.environment[self.posx,self.posy-1] 
            self.sensor_werte[Const.LINKS] = self.umgebung.environment[self.posx-1,self.posy] 
            sensor_werte = self.sensor_werte
        else:
            sensor_werte[Const.RECHTS] = self.umgebung.environment[posx+1,posy] 
            sensor_werte[Const.UNTEN] = self.umgebung.environment[posx,posy+1] 
            sensor_werte[Const.OBEN] = self.umgebung.environment[posx,posy-1] 
            sensor_werte[Const.LINKS] = self.umgebung.environment[posx-1,posy]            
            
        return sensor_werte

# Der Controller
class Controller(object): 

    def move_me_q(self,posx=-1,posy=-1,dimx=10,dimy=10,Q={}):
        # Clone = Hirnentnahme
        agent_clone = copy.deepcopy(self.agent)
        # Hirntransplantation?
        if Q != {}:
            agent_clone.Q = Q
        agent_clone.init_agent()
        # Neue Umbegung
        umgebung_neu = Umgebung(dimx,dimy)
        agent_clone.set_umgebung(umgebung_neu)
        umgebung_neu.agent = agent_clone

        # Pos
        if posx == -1 and posy == -1:
            agent_clone.random_pos()
            posx = agent_clone.posx
            posy = agent_clone.posy
        else:
            agent_clone.set_pos(posx,posy)
        umgebung_neu.init_environment()
        # Agent hat besucht
        umgebung_neu.change_environment(agent_clone.posx,agent_clone.posy,Const.BESUCHT) 
        # Ausgabe
        for run_agent_run in range((dimx - 2) * (dimy - 2)):
            if print_flag == True:
                clear_output(wait=True) 
            agent_clone.move_me_q()
            umgebung_neu.change_environment(agent_clone.posx,agent_clone.posy,Const.BESUCHT)
            if umgebung_neu.all_visited() == True:
                break
        if Q != {}:
            agent_clone.print_Q()        
        return {'moves':agent_clone.moves,'moves2u':agent_clone.moves_2_u,'moves2b':agent_clone.moves_2_b,'moves2w':agent_clone.moves_2_w}

    def print_move_me_q_all(self,dimx=10,dimy=10,Q={}):
        # Für jedes Feld in der Umgebung den Agenten wandern lassen
        for y in range(1,dimx-1):
            for x in range(1,dimy-1):
                self.move_me_q(posx=x,posy=y,dimx=dimx,dimy=dimy,Q=Q)

 

    def collect_stats(self,agent,episode,max_q_moves2u,max_episode_moves2u,max_all_moves2u,max_moves2u):
        # Statistiken für die Agenten Performance sammeln
        # Summe aller Moves 2 U
        all_moves_moves2u = [] 
        # Summen
        sum_moves2u = 0.0 # Bewegungen zu unbesuchten Feldern
        sum_moves2b = 0.0 # Bewegungen zu besuchten Feldern
        sum_moves2w = 0.0 # Bewegungen in die Wand
        # Belohnung
        self.score_agent.append(agent.score)
        # Schritte
        self.moves_agent.append(agent.moves)

        # Falls nur alle x Epochen die Evaluierung stattfinden sollte
        if episode%1 == 0: 
            all_moves2u = []
            for y in range(1, self.eval_hoehe - 1):
                for x in range(1, self.eval_breite - 1):
                    move_stats = self.print_move_me_q(print_flag = False, posx = x, posy = y, \
                                                      dimx = self.eval_breite, dimy = self.eval_hoehe)
                    sum_moves2u += move_stats['moves2u']
                    sum_moves2b += move_stats['moves2b']
                    sum_moves2w += move_stats['moves2w']
                    all_moves2u.append(move_stats['moves2u'])
            self.moves2u_agent.append(sum_moves2u)
            self.moves2b_agent.append(sum_moves2b)
            self.moves2w_agent.append(sum_moves2w)
            if sum_moves2u > max_moves2u:
                max_moves2u = sum_moves2u
                max_q_moves2u = copy.deepcopy(agent.Q)
                max_episode_moves2u = episode
                max_all_moves2u = all_moves2u

            #sum_moves2u = 0
            #sum_moves2b = 0
            #sum_moves2w = 0
        return max_q_moves2u, max_episode_moves2u, max_all_moves2u, max_moves2u, sum_moves2u

# Zufallsgenerator 
random.seed(42)

# Umgebungsdimensionen
train_breite = 5
train_hoehe = 5
eval_breite = 5
eval_hoehe = 5
test_breite = 10
test_hoehe = 10  
# Game Loop 
episoden = 100
iterationen = (train_breite - 2) * (train_hoehe - 2) * 4 # 4 Richtungen mal der Anzahl der Felder
# Q
gamma = 0.8 # Abschlag für max Q-Wert
alpha_min = 0.1 # Lernraten Untergrenze
alpha_max = 1.0 # Lernraten Obergrenze
alpha_ratio = 1.0
alpha = lambda step: round(max(0.0, (((alpha_max - alpha_min) / episoden / alpha_ratio)) * ((episoden / alpha_ratio) - step ))),4 

epsilon_min = 0.1 # Auswahlsuntergrenze für zufällige Aktion
epsilon_max = 1.0 # Auswahlsobergrenze für zufällige Aktion
epsilon_ratio = 1.0
epsilon = lambda step: round(1.0 - max(0.0, (((epsilon_max - epsilon_min) / (episoden / epsilon_ratio)) * ((episoden / epsilon_ratio) - step))),4)

# Graphen
status_agent = {}
score_agent = []
moves_agent = []
moves2u_agent = []
moves2b_agent = []
moves2w_agent = []

# Die ganze Schleife
# Setup des Agenten und der Umgebung
umgebung = Umgebung(train_breite,train_hoehe)
agent = Agent(1,1,umgebung,gamma,alpha(0),epsilon(0))  
umgebung.agent = agent

# Lernen mittels Q-learning

# Das Trainieren des Agenten für Epochen und Iterationen
# Max Q-Tabelle
max_q_moves2u = {}
max_all_moves2u = 0
max_episode_moves2u = 0  
max_moves2u = 0
# Kontrollschleife 
for episode in range(episoden):
    iterationen_counter = 0
    umgebung.init_environment()
    umgebung.change_environment(agent.posx,agent.posy,Const.BESUCHT) 
    while True:
        status_agent = agent.action(print_flag,alpha(episode))
        umgebung.change_environment(agent.posx,agent.posy,Const.BESUCHT)
        time.sleep(0.00)
        iterationen_counter += 1
        if iterationen_counter > iterationen or umgebung.all_visited():
            break
    # Statistiken sammeln
    max_q_moves2u, max_episode_moves2u, max_all_moves2u, max_moves2u, sum_moves2u = controller.collect_stats(controller.agent,episode, max_q_moves2u,max_episode_moves2u,max_all_moves2u,max_moves2u)
    # Schritte benötigt
    print("Episode: {} Schritte/2U: {} {} Alpha: {} Epsilon: {}"\
        .format(episode, agent.moves,sum_moves2u,alpha(episode), epsilon(episode)))      
    # Agent initialisieren bis auf Q-Tabelle
    agent.init_agent(epsilon=epsilon(episode))
# Moves2U Replay
controller.print_move_me_q_all(dimx=5,dimy=5,Q=max_q_moves2u)