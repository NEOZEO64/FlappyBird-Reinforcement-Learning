# Flappy Bird, wrote on April 24th, 2024

import pygame as pg
import random as r
import numpy as np

#import reinforce_agent

WINDOW_WIDTH = 800
WINDOW_HEIGHT = 480


speed = WINDOW_WIDTH/250
pipeDist = WINDOW_WIDTH/5
gravity = 0.4

gameOverTime = 100

pg.init()
clock = pg.time.Clock()

fps = 999

floatFPS = fps
screen = pg.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT)) 


def map(x, fromInterval, toInterval):
    if x > fromInterval[1]:
        return toInterval[1]
    if x < fromInterval[0]:
        return toInterval[0]

    return toInterval[0] + (toInterval[1]-toInterval[0])* (x-fromInterval[0])/(fromInterval[1]-fromInterval[0])

def fpsCoeff():
    currentFps = clock.get_fps()
    if currentFps == 0:
        return 1
    else:
        return fps / currentFps

class Bird(object):
    w = WINDOW_WIDTH/25
    h = w/1.3
    x = WINDOW_WIDTH*0.3

    pic = pg.transform.scale(pg.image.load("./res/Bird.bmp"), (w,h))
    pic2 = pg.transform.scale(pg.image.load("./res/Bird2.bmp"), (w,h))

    def __init__(self):
        self.y=WINDOW_HEIGHT/2
        self.vY = 0
        self.wingsUp = 1
        self.score = 0

    def move(self):
        self.y += self.vY*fpsCoeff()
        self.vY += gravity # add gravity
        
        self.wingsUp += 1
        self.wingsUp %= 10

    def flap(self):
        self.vY = -5

    def show(self):
        angle = -self.vY*2

        if self.wingsUp < 5:
            screen.blit(pg.transform.rotate(Bird.pic,angle),(Bird.x,self.y))
        else:
            screen.blit(pg.transform.rotate(Bird.pic2,angle),(Bird.x,self.y))


class PipePair(object):
    w = WINDOW_WIDTH /16
    h = WINDOW_HEIGHT*0.7

    gap = WINDOW_HEIGHT*0.3
    margin = 10

    pic = pg.image.load("./res/pipe.bmp")
    pic = pg.transform.scale(pic, (w,h))
    pic_180 = pg.transform.rotate(pic,180)
    vX = speed

    pipeNum = WINDOW_WIDTH / pipeDist
    
    collideIndex = int(pipeNum * Bird.x / WINDOW_WIDTH)

    def __init__(self):
        self.x = WINDOW_WIDTH
        self.y = r.randint(int(PipePair.margin), int(WINDOW_HEIGHT-PipePair.gap-Environment.groundH-PipePair.margin))
        self.scored = False

    def move(self): # return if scored
        ox = self.x
        self.x -= PipePair.vX*fpsCoeff()
        if ox > Bird.x and self.x < Bird.x and self.scored == False:
            return True
        return False

    def show(self):
        screen.blit(PipePair.pic_180,(self.x,self.y-self.h))
        screen.blit(PipePair.pic,(self.x,self.y + PipePair.gap))

class Environment:
    backPic = pg.transform.scale(pg.image.load("./res/Background.bmp"), (WINDOW_WIDTH,WINDOW_HEIGHT))
    backPicW = backPic.get_width()

    groundPic = pg.transform.scale(pg.image.load("./res/Ground.bmp"), (WINDOW_WIDTH/3,WINDOW_WIDTH/9))
    groundPicH = groundPic.get_height()
    groundPicW = groundPic.get_width()
    groundH = WINDOW_HEIGHT/10

    def __init__(self):
        self.groundX = 0
        self.backX = 0
        self.pipePairs = []

        self.started = False
    
    def getPipeCollideIndex(self):
        if len(self.pipePairs)>= PipePair.pipeNum-1:
            return PipePair.collideIndex
        else:
            return 0

    def update(self, bird):
        # move ground
        self.groundX -= speed*fpsCoeff()
        if self.groundX <= -Environment.groundPicW:
            self.groundX = 0

        # move background
        self.backX -= speed/2 *fpsCoeff()
        if self.backX <= -Environment.backPicW:
            self.backX = 0

        # move pipe pairs
        for pipePair in self.pipePairs:
            if pipePair.move():
                bird.score += 1

        # manage pipe pairs
        if len(self.pipePairs) == 0 or WINDOW_WIDTH - (self.pipePairs[-1].x + PipePair.w) > pipeDist:
            self.pipePairs.append(PipePair())
        
        if len(self.pipePairs) > 0: 
            if self.pipePairs[0].x + PipePair.w < 0:
                del self.pipePairs[0]
    
    def collide(self,bird):
        if bird.y + Bird.h > WINDOW_HEIGHT-Environment.groundH:
            return True
        
        for pipePair in self.pipePairs:
            if pipePair.x < bird.x < pipePair.x + PipePair.w or pipePair.x < bird.x + Bird.w < pipePair.x + PipePair.w:
                if bird.y + Bird.h > pipePair.y + PipePair.gap or bird.y < pipePair.y:
                    return True
        return False

    def show(self):
        # show background pieces
        for x in range(int(self.backX),WINDOW_WIDTH,WINDOW_WIDTH):
            screen.blit(self.backPic,(x,-Environment.groundH+4))

        # show pipes
        for i, pipePair in enumerate(self.pipePairs):
            if i == self.getPipeCollideIndex():
                pg.draw.rect(screen, (255,0,0), (pipePair.x,0,PipePair.w, WINDOW_HEIGHT))
            pipePair.show()

        # show ground pieces
        for x in range(int(self.groundX),WINDOW_WIDTH,Environment.groundPicW):
            screen.blit(Environment.groundPic,(x,WINDOW_HEIGHT-Environment.groundH))


class RMgmt: # Reward Management

    xInterval = [-100, 100]
    yTopInterval = [0, WINDOW_HEIGHT-PipePair.gap]
    yBottomInterval = [0, WINDOW_HEIGHT-PipePair.gap]
    yInterval = [0, WINDOW_HEIGHT-PipePair.gap]
    yCenterInterval = [-WINDOW_HEIGHT, WINDOW_HEIGHT]
    vYInterval = [-20,40]
    neuroInterval1 = [0, 32]
    neuroInterval2 = [0, 16]

    alpha = 1
    gamma = 0.8

    def __init__(self, bird, environment):
        self.score = 0

        # boundaries:
        self.Q = {} # keys: game state, value: float value, if >0.5: flap!

        '''
        for x in range(RMgmt.neuroInterval2[0], RMgmt.neuroInterval2[1]):
            for yTop in range(RMgmt.neuroInterval2[0], RMgmt.neuroInterval2[1]):
                for yBottom in range(RMgmt.neuroInterval2[0], RMgmt.neuroInterval2[1]):
                    for y in range(RMgmt.neuroInterval1[0], RMgmt.neuroInterval1[1]):
                        for vY in range(RMgmt.neuroInterval2[0], RMgmt.neuroInterval2[1]):
                            self.Q[x, yTop, yBottom, y, vY] = [0.5, 0.5]
        '''

    def getQ(self, state):
        if state not in self.Q:
            self.Q[state] = [0.5, 0.5]
        return self.Q[state]
    '''
    def mapInfo2State(x, yTop, yBottom, y, vY): # map real world values to 0-64 integer values
        return (map(x, RMgmt.xInterval, RMgmt.neuroInterval2),
                map(yTop, RMgmt.yTopInterval, RMgmt.neuroInterval2),
                map(yBottom, RMgmt.yBottomInterval, RMgmt.neuroInterval2),
                map(y,RMgmt.yInterval, RMgmt.neuroInterval1), # use more table entries
                map(vY, RMgmt.vYInterval, RMgmt.neuroInterval2),
            )
    

    def mapState2Info(state): # map real world values to 0-64 integer values
        (x, yTop, yBottom, y, vY) = state
        return [map(x, RMgmt.neuroInterval2, RMgmt.xInterval),
                map(yTop, RMgmt.neuroInterval2, RMgmt.yTopInterval),
                map(yBottom, RMgmt.neuroInterval2, RMgmt.yBottomInterval),
                map(y, RMgmt.neuroInterval1, RMgmt.yInterval), # use more table entries
                map(vY, RMgmt.neuroInterval2, RMgmt.vYInterval)
                ]
    '''
    
    def mapInfo2State(yCenter, y, vY): # map real world values to 0-64 integer values
        return (map(yCenter, RMgmt.yCenterInterval, RMgmt.neuroInterval1),
                map(y,RMgmt.yInterval, RMgmt.neuroInterval1), # use more table entries
                map(vY, RMgmt.vYInterval, RMgmt.neuroInterval2),
            )

    def mapState2Info(state): # map real world values to 0-64 integer values
        (yCenter, y, vY) = state
        return [map(yCenter, RMgmt.neuroInterval1,RMgmt.yCenterInterval),
                map(y,RMgmt.neuroInterval1, RMgmt.yInterval), # use more table entries
                map(vY, RMgmt.neuroInterval2, RMgmt.vYInterval)
                ]

    def getState(self, bird, enviroment):
        if len(environment.pipePairs) >= 1:
            pipePair = environment.pipePairs[environment.getPipeCollideIndex()]
            #return RMgmt.mapInfo2State(pipePair.x - (bird.x+Bird.w), pipePair.y - (bird.y+Bird.h/2), pipePair.y + PipePair.gap - (bird.y + Bird.h/2), bird.y, bird.vY )        
            return RMgmt.mapInfo2State(pipePair.y + PipePair.gap/2 - (bird.y+Bird.h/2), bird.y, bird.vY )        
        #return RMgmt.mapInfo2State(WINDOW_WIDTH - (bird.x+Bird.w), WINDOW_HEIGHT/2 - (bird.y+Bird.h/2), WINDOW_HEIGHT/2 - (bird.y + Bird.h/2), bird.y, bird.vY )
        return RMgmt.mapInfo2State(WINDOW_HEIGHT/2 - (bird.y+Bird.h/2), bird.y, bird.vY )

    def updateQ(self, oldState, newState, bird, gameRun, pipePair, action): # action 0 for not flap, action 1 for flap
        self.Q[oldState] = self.getQ(oldState)
        self.Q[oldState][action] = (1-RMgmt.alpha) * self.getQ(oldState)[action] + RMgmt.alpha * (RMgmt.calcReward(bird, gameRun, pipePair) + self.gamma * self.getQ(newState)[action])

    def decide(self, state):
        actions = self.getQ(state) # action 0 for not flap, action 1 for flap
        if actions[0] == actions[1]:
            return r.randint(0,100)>90
        return actions[1] > actions[0]
            
    def calcReward(bird, gameRun, pipePair):
        if gameRun == False:
            return -1000
        else:
            return bird.score * 10 - np.linalg.norm(np.array([pipePair.y + PipePair.gap/2 - bird.y]))/20

    def show(self, bird, environment, state):
        #(x, yTop, yBottom, y, vY) = RMgmt.mapState2Info(state)
        (yC, y, vY) = RMgmt.mapState2Info(state)

        if len(environment.pipePairs) > 0:
            # to top pipe
            pg.draw.line(screen, (0,0,255), (bird.x + Bird.w, bird.y + Bird.h/2), (bird.x+Bird.w +20, bird.y+Bird.h/2+yC))

            # to bottom pipe
            #pg.draw.line(screen, (0,0,255), (startX, startY), (botPipeX, botPipeY))


bird = Bird()
environment = Environment()
rMgmt = RMgmt(bird, environment)

# WORKING LOOP
work = True
while work:
    # RESET
    bird = Bird()
    environment = Environment()
    #started = False

    # MAIN GAME RUN LOOP
    gameRun = True
    while gameRun == True:
        # INTERACTION
        for event in pg.event.get():
            if event.type == pg.QUIT:
                work = False
                gameRun = False
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_SPACE or event.key == pg.K_d:
                    #started = True
                    bird.flap()
                elif event.key == pg.K_ESCAPE:
                    work = False
                    gameRun = False
                elif event.key == pg.K_DOWN:
                    floatFPS *= 0.5
                    fps = int(floatFPS)
                elif event.key == pg.K_UP:
                    floatFPS *= 2
                    fps = int(floatFPS)

        # GAME PHYSICS        
        environment.update(bird)
        gameRun = gameRun and not environment.collide(bird)

        oldState = rMgmt.getState(bird, environment)

        if rMgmt.decide(oldState):
            #bird.flap()
            bird.move()
            newState = rMgmt.getState(bird,environment)
            rMgmt.updateQ(oldState, newState, bird, gameRun, environment.pipePairs[environment.getPipeCollideIndex()],1)
        else:
            bird.move()
            newState = rMgmt.getState(bird,environment)
            rMgmt.updateQ(oldState, newState, bird, gameRun, environment.pipePairs[environment.getPipeCollideIndex()],0)

        # SHOW
        environment.show() # includes rendering UI
        bird.show()

        rMgmt.show(bird, environment, newState)
        
        #print("Reward:", RMgmt.calcReward(bird, gameRun,environment.pipePairs[environment.getPipeCollideIndex()]))

        pg.display.flip()

        clock.tick(fps)

    # GAME OVER LOOP removed

pg.quit()