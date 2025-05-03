#--------------------------------------------------------------------------------
#------- PLANTILLA DE CÓDIGO ----------------------------------------------------
#------- Coceptos básicos de PDI-------------------------------------------------
#------- Por: Harold José Urquijo Durán harold.urquijo@udea.edu.co --------------
#-------      CC 1193093197 -----------------------------------------------------
#-------      Estudiante de ingeniería de Telecomunicaciones --------------------
#-------      Ferney Mejía Pérez ferney.mejiap@udea.edu.co-----------------------
#-------      CC 1026159558 -----------------------------------------------------
#-------      Estudiante de ingeniería de Telecomunicaciones --------------------
#------- Curso Básico de Procesamiento de Imágenes y Visión Artificial-----------
#------- 2 Mayo de 2025----------------------------------------------------------
#--------------------------------------------------------------------------------



#--------------------------------------------------------------------------
#-- 1. Librerías necesarias ---------------------------------------------
#--------------------------------------------------------------------------

import pygame, random, time               # Librerías para juego, aleatoriedad y tiempo
from pygame.locals import *               # Eventos del teclado y ventana
import cv2                                # OpenCV para detección facial
import threading                          # Permite ejecutar captura facial en paralelo

#--------------------------------------------------------------------------
#-- 2. Parámetros de juego y dimensión de ventana ------------------------
#--------------------------------------------------------------------------

SCREEN_WIDHT = 800                        # Ancho de la ventana principal del juego
SCREEN_HEIGHT = 600                       # Alto de la ventana principal del juego

SPEED = 20                                # Velocidad inicial del pájaro
GRAVITY = 2.5                             # Gravedad que afecta el movimiento (no usada directamente)
GAME_SPEED = 15                           # Velocidad a la que se mueven los objetos (tubos, suelo)

GROUND_WIDHT = 2 * SCREEN_WIDHT           # Ancho total del suelo (doble para desplazamiento)
GROUND_HEIGHT = 100                       # Alto del suelo visual del juego

PIPE_WIDHT = 80                           # Ancho de los tubos
PIPE_HEIGHT = 500                         # Alto de los tubos
PIPE_GAP = 150                            # Espacio vertical entre tubos superior e inferior

#--------------------------------------------------------------------------
#-- 3. Carga de audios del juego ------------------------------------------
#--------------------------------------------------------------------------

wing = 'assets/audio/wing.wav'            # Sonido al saltar
hit = 'assets/audio/hit.wav'              # Sonido al colisionar

pygame.mixer.init()                       # Inicializa el sistema de audio

#--------------------------------------------------------------------------
#-- 4. Inicialización de detección facial -------------------------------
#--------------------------------------------------------------------------

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades +
    'haarcascade_frontalface_default.xml')  # Carga clasificador Haar para rostros frontales

cap = cv2.VideoCapture(0)                 # Captura desde cámara (0 = predeterminada)
rostro_y = SCREEN_HEIGHT / 2              # Valor inicial en Y del rostro (centro de pantalla)
frame_global = None                       # Frame compartido para mostrar cámara en juego

#--------------------------------------------------------------------------
#-- 5. Mostrar puntaje en pantalla ----------------------------------------
#--------------------------------------------------------------------------

def mostrar_score(pantalla, score):
    fuente = pygame.font.SysFont("Arial", 30)                            # Fuente usada
    texto = fuente.render(f"Score: {score}", True, (255, 255, 255))      # Render del texto
    pantalla.blit(texto, (10, 10))                                       # Dibuja arriba a la izquierda

#--------------------------------------------------------------------------
#-- 6. Captura y detección facial (paralelo) ----------------------------
#--------------------------------------------------------------------------

def capturar_rostro():
    global rostro_y, frame_global
    while True:
        ret, frame = cap.read()                                          # Lee imagen de la cámara
        if not ret:
            continue

        gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)                  # Convierte a escala de grises
        rostros = face_cascade.detectMultiScale(gris, 1.3, 5)           # Aplica Haar Cascade

        if len(rostros) > 0:
            x, y, w, h = rostros[0]                                     # Primer rostro detectado
            rostro_y = y + h // 2                                       # Centro vertical del rostro
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2) # Dibuja rectángulo verde

        frame_global = cv2.resize(frame, (320, 240))                    # Redimensiona para mostrar en juego
        cv2.imshow('Camara', frame)                                     # Muestra ventana OpenCV
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

#--------------------------------------------------------------------------
#-- 7. Ejecución paralela de la cámara -----------------------------------
#--------------------------------------------------------------------------

t_camara = threading.Thread(target=capturar_rostro)
t_camara.daemon = True
t_camara.start()

#--------------------------------------------------------------------------
#-- 8. Clase Bird (pájaro controlado por rostro) -------------------------
#--------------------------------------------------------------------------

class Bird(pygame.sprite.Sprite):

    def __init__(self):
        pygame.sprite.Sprite.__init__(self)

        # Carga de sprites para animación del pájaro
        self.images =  [pygame.image.load('assets/sprites/bluebird-upflap.png').convert_alpha(),
                        pygame.image.load('assets/sprites/bluebird-midflap.png').convert_alpha(),
                        pygame.image.load('assets/sprites/bluebird-downflap.png').convert_alpha()]

        self.speed = SPEED
        self.current_image = 0
        self.image = self.images[0]                                     # Imagen inicial
        self.mask = pygame.mask.from_surface(self.image)               # Máscara para colisiones

        self.rect = self.image.get_rect()
        self.rect[0] = SCREEN_WIDHT / 6                                 # Posición X inicial
        self.rect[1] = SCREEN_HEIGHT / 2                                # Posición Y inicial

    def update(self, y_rostro):
        self.current_image = (self.current_image + 1) % 3               # Cicla entre las 3 imágenes
        self.image = self.images[self.current_image]                    # Actualiza sprite
        self.rect[1] = y_rostro                                         # Controlado por la altura del rostro

    def bump(self):
        self.speed = -SPEED                                             # Movimiento hacia arriba (si fuera por teclado)

    def begin(self):
        self.current_image = (self.current_image + 1) % 3
        self.image = self.images[self.current_image]                    # Animación inicial (parpadeo)

#--------------------------------------------------------------------------
#-- 9. Clase Pipe (tubos del juego) --------------------------------------
#--------------------------------------------------------------------------

class Pipe(pygame.sprite.Sprite):

    def __init__(self, inverted, xpos, ysize):
        pygame.sprite.Sprite.__init__(self)

        self.image = pygame.image.load('assets/sprites/pipe-green.png').convert_alpha()
        self.image = pygame.transform.scale(self.image, (PIPE_WIDHT, PIPE_HEIGHT))

        self.rect = self.image.get_rect()
        self.rect[0] = xpos

        if inverted:
            self.image = pygame.transform.flip(self.image, False, True) # Tubo superior (invertido)
            self.rect[1] = - (self.rect[3] - ysize)
        else:
            self.rect[1] = SCREEN_HEIGHT - ysize                         # Tubo inferior

        self.mask = pygame.mask.from_surface(self.image)                # Máscara para colisiones

    def update(self):
        self.rect[0] -= GAME_SPEED                                      # Movimiento hacia la izquierda

#--------------------------------------------------------------------------
#-- 10. Clase Ground (suelo del juego) -----------------------------------
#--------------------------------------------------------------------------

class Ground(pygame.sprite.Sprite):

    def __init__(self, xpos):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load('assets/sprites/base.png').convert_alpha()
        self.image = pygame.transform.scale(self.image, (GROUND_WIDHT, GROUND_HEIGHT))

        self.mask = pygame.mask.from_surface(self.image)

        self.rect = self.image.get_rect()
        self.rect[0] = xpos
        self.rect[1] = SCREEN_HEIGHT - GROUND_HEIGHT

    def update(self):
        self.rect[0] -= GAME_SPEED                                      # Suelo se desplaza

#--------------------------------------------------------------------------
#-- 11. Funciones auxiliares de tubería ----------------------------------
#--------------------------------------------------------------------------

def is_off_screen(sprite):
    return sprite.rect[0] < -(sprite.rect[2])                           # Detecta si salió completamente

def get_random_pipes(xpos):
    size = random.randint(100, 300)
    pipe = Pipe(False, xpos, size)
    pipe_inverted = Pipe(True, xpos, SCREEN_HEIGHT - size - PIPE_GAP)
    return pipe, pipe_inverted                                          # Retorna par de tubos

#--------------------------------------------------------------------------
#-- 12. Inicialización de Pygame y entorno gráfico ------------------------
#--------------------------------------------------------------------------

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDHT + 320, SCREEN_HEIGHT))   # +320 px para cámara al costado\pygame.display.set_caption('Flappy Bird')

# Fondo y mensaje de inicio
BACKGROUND = pygame.image.load('assets/sprites/background-day.png')
BACKGROUND = pygame.transform.scale(BACKGROUND, (SCREEN_WIDHT, SCREEN_HEIGHT))
BEGIN_IMAGE = pygame.image.load('assets/sprites/message.png').convert_alpha()

# Grupo de sprites del pájaro
bird_group = pygame.sprite.Group()
bird = Bird()
bird_group.add(bird)

# Grupo de sprites del suelo
ground_group = pygame.sprite.Group()
for i in range(2):
    ground = Ground(GROUND_WIDHT * i)
    ground_group.add(ground)

# Grupo de tubos iniciales
pipe_group = pygame.sprite.Group()
for i in range(2):
    pipes = get_random_pipes(SCREEN_WIDHT * i + 800)
    pipe_group.add(pipes[0])
    pipe_group.add(pipes[1])

# Reloj para controlar FPS
clock = pygame.time.Clock()
begin = True
score = 0

#--------------------------------------------------------------------------
#-- 13. Pantalla de inicio del juego --------------------------------------
#--------------------------------------------------------------------------

while begin:
    clock.tick(15)                                                      # Control de FPS en espera
    ret, frame = cap.read()
    if ret:
        cv2.imshow('Camara', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
        if event.type == KEYDOWN:
            if event.key == K_SPACE or event.key == K_UP:
                bird.bump()
                pygame.mixer.music.load(wing)
                pygame.mixer.music.play()
                begin = False

    screen.blit(BACKGROUND, (0, 0))
    screen.blit(BEGIN_IMAGE, (120, 150))

    if is_off_screen(ground_group.sprites()[0]):
        ground_group.remove(ground_group.sprites()[0])
        new_ground = Ground(GROUND_WIDHT - 20)
        ground_group.add(new_ground)

    bird.begin()
    ground_group.update()

    bird_group.draw(screen)
    ground_group.draw(screen)

    pygame.display.update()

#--------------------------------------------------------------------------
#-- 14. Ciclo principal del juego -----------------------------------------
#--------------------------------------------------------------------------

while True:
    clock.tick(15)                                                      # Velocidad de refresco

    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
        if event.type == KEYDOWN:
            if event.key == K_SPACE or event.key == K_UP:
                bird.bump()
                pygame.mixer.music.load(wing)
                pygame.mixer.music.play()

    screen.blit(BACKGROUND, (0, 0))                                     # Dibuja fondo

    # Actualiza suelo y tubos
    if is_off_screen(ground_group.sprites()[0]):
        ground_group.remove(ground_group.sprites()[0])
        new_ground = Ground(GROUND_WIDHT - 20)
        ground_group.add(new_ground)

    if is_off_screen(pipe_group.sprites()[0]):
        pipe_group.remove(pipe_group.sprites()[0])
        pipe_group.remove(pipe_group.sprites()[0])
        pipes = get_random_pipes(SCREEN_WIDHT * 2)
        pipe_group.add(pipes[0])
        pipe_group.add(pipes[1])

    # Control del pájaro con rostro
    bird.update(rostro_y)
    ground_group.update()
    pipe_group.update()

    # Puntaje (cuando el pájaro supera un tubo sin colisión)
    for pipe in pipe_group:
        if pipe.rect.right < bird.rect.left and not hasattr(pipe, 'pasado'):
            score += 0.5
            pipe.pasado = True

    bird_group.draw(screen)
    pipe_group.draw(screen)
    ground_group.draw(screen)

    mostrar_score(screen, int(score))

    # Zona derecha para mostrar cámara
    pygame.draw.rect(screen, (0, 0, 0), (SCREEN_WIDHT, 0, 320, SCREEN_HEIGHT))
    if frame_global is not None:
        cam_surface = pygame.image.frombuffer(
            cv2.cvtColor(frame_global, cv2.COLOR_BGR2RGB).tobytes(),
            frame_global.shape[1::-1],
            "RGB"
        )
        screen.blit(cam_surface, (SCREEN_WIDHT, 20))

    pygame.display.update()

    # Detecta colisión con tubos o suelo
    if (pygame.sprite.groupcollide(bird_group, ground_group, False, False, pygame.sprite.collide_mask) or
        pygame.sprite.groupcollide(bird_group, pipe_group, False, False, pygame.sprite.collide_mask)):
        pygame.mixer.music.load(hit)
        pygame.mixer.music.play()
        pygame.time.delay(300)
        cap.release()
        cv2.destroyAllWindows()
        pygame.quit()
        sys.exit()

#--------------------------------------------------------------------------
#---------------------------  FIN DEL PROGRAMA ----------------------------
#--------------------------------------------------------------------------
