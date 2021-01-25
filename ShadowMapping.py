
from OpenGL.GL import *
from OpenGL.GL.shaders import *
import glfw, pyrr, math, ctypes, random
import numpy as np
from PIL import Image
from time import sleep

glfw.init()

glfw.window_hint(glfw.SAMPLES, 4)

app = glfw.create_window(500, 400, "Shadow Mapping Final", None, None)

glfw.make_context_current(app)

v = """
#version 430
in layout(location=0) vec3 posicao;
in layout(location=1) vec2 textura;
uniform mat4 view;
uniform vec3 escala;
uniform vec3 deform;
uniform vec3 translate;
uniform vec3 pos;
uniform float X;
uniform float Y;
uniform float rX;
uniform float rY;
out vec3 outpos;
out vec3 outpos2;
void main(){
	vec3 p = (posicao*escala)+deform;
	p = vec3(p.x,p.y*cos(X)-sin(X)*p.z,p.y*sin(X)+cos(X)*p.z);
	p = vec3(cos(Y)*p.x+sin(Y)*p.z,p.y,cos(Y)*p.z-sin(Y)*p.x);
	p = p+translate+pos;
	outpos2 = p;
	p = vec3(cos(rY)*p.x+sin(rY)*p.z,p.y,cos(rY)*p.z-sin(rY)*p.x);
	p = vec3(p.x,p.y*cos(rX)-sin(rX)*p.z,p.y*sin(rX)+cos(rX)*p.z);
	outpos = p;
	gl_Position = view*vec4(p,1);
}
"""

f = """
#version 430
uniform vec3 cor;
uniform int filtro;
uniform sampler2D sombra;
uniform vec3 shadowpos;
uniform float shadowdir;
in vec3 outpos;
in vec3 outpos2;
void main(){
	if(filtro==0){
		vec3 p = vec3(outpos2.x,outpos2.y,outpos2.z)+vec3(shadowpos);
		p = vec3(p.x,p.y*cos(shadowdir)-sin(shadowdir)*p.z,p.y*sin(shadowdir)+cos(shadowdir)*p.z);
		p.z+=0.1;
		if(texture(sombra,vec2(.5)+vec2(p.xy/200)).r<-p.z){
			gl_FragColor = vec4(cor/2,1);
		}else{
			gl_FragColor = vec4(cor,1);
		}
		if(p.x<-100 || p.y<-100 || p.x>100 || p.y>100){
			gl_FragColor = vec4(cor,1);
		}
		//gl_FragColor = texture(sombra,vec2(.5)+vec2(p.xy/100));
	}
	if(filtro==1){
		gl_FragColor = vec4(vec3(-outpos.z),1);
	}
}
"""

shader = compileProgram(compileShader(v, GL_VERTEX_SHADER), compileShader(f, GL_FRAGMENT_SHADER))

tudo = [-1,-1,0,0,1,
        1,-1,0,1,1,
		1,1,0,1,0,
		-1,1,0,0,0]

tudo = np.array(tudo, np.float32)

VBO = glGenBuffers(1)
glBindBuffer(GL_ARRAY_BUFFER, VBO)
glBufferData(GL_ARRAY_BUFFER, len(tudo)*4, tudo, GL_STATIC_DRAW)

glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 20, ctypes.c_void_p(0))
glEnableVertexAttribArray(0)

glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 20, ctypes.c_void_p(12))
glEnableVertexAttribArray(1)

glUseProgram(shader)

view = pyrr.matrix44.create_perspective_projection_matrix(60, 5/4, .1, 1000)
p = glGetUniformLocation(shader, "view")
glUniformMatrix4fv(p, 1, GL_FALSE, view)

glEnable(GL_DEPTH_TEST)
glEnable(GL_TEXTURE_2D)
glEnable(GL_MULTISAMPLE)

# Framebuffer
tf = glGenTextures(1)
glBindTexture(GL_TEXTURE_2D, tf)
glTexImage2D(GL_TEXTURE_2D, 0, GL_R32F, 4000, 3200, 0, GL_RED, GL_UNSIGNED_BYTE, None)
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
f = glGenFramebuffers(1)
r = glGenRenderbuffers(1)
glBindFramebuffer(GL_FRAMEBUFFER, f)
glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, tf, 0)
glBindRenderbuffer(GL_RENDERBUFFER, r)
glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH24_STENCIL8, 4000, 3200)
glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, r)
glBindRenderbuffer(GL_RENDERBUFFER, 0)
glBindFramebuffer(GL_FRAMEBUFFER, 0)

# Cenario
arvores = []
for x in range(20):
	arvores+=[[random.randint(-20,20),random.randint(-20,20)]]

# Gameplay
pos = [0,0,0]
rotX = rotY = 0
tvec = glfw.get_time()

# FPS
fps = 0
tfps = glfw.get_time()

# direção e posição da luz
dir = 90

while not glfw.window_should_close(app):
	glfw.swap_buffers(app)
	glfw.poll_events()
	# Sombreamento
	view = pyrr.matrix44.create_orthogonal_projection_matrix(-100, 100, -100, 100, .1, 1000)
	p = glGetUniformLocation(shader, "view")
	glUniformMatrix4fv(p, 1, GL_FALSE, view)
	glViewport(0, 0, 4000, 3200)
	glBindFramebuffer(GL_FRAMEBUFFER, f)
	glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
	# Filtro
	glUniform1i(glGetUniformLocation(shader, "filtro"), 1)
	# Gameplay
	temp1 = dir+180
	glUniform1f(glGetUniformLocation(shader, "rX"), dir*math.pi/180)
	glUniform1f(glGetUniformLocation(shader, "rY"), 0)
	glUniform3f(glGetUniformLocation(shader, "pos"), pos[0], pos[1]+100*math.sin(temp1*math.pi/180), pos[2]+100*math.cos(temp1*math.pi/180))
	glUniform3f(glGetUniformLocation(shader, "shadowpos"), 0, 100*math.sin(temp1*math.pi/180), 100*math.cos(temp1*math.pi/180))
	glUniform1f(glGetUniformLocation(shader, "shadowdir"), dir*math.pi/180)
	dir+=.1
	if dir > 180:
		dir = 0
	# Cenario
	glUniform3f(glGetUniformLocation(shader, "cor"), 1, 0, 0)
	glUniform3f(glGetUniformLocation(shader, "escala"),2000,2000,1)
	glUniform3f(glGetUniformLocation(shader, "deform"),0,0,0)
	glUniform3f(glGetUniformLocation(shader, "translate"),0,-5,0)
	glUniform1f(glGetUniformLocation(shader, "X"), math.pi/2)
	glUniform1f(glGetUniformLocation(shader, "Y"), 0)
	glDrawArrays(GL_POLYGON, 0, 4)
	glUniform3f(glGetUniformLocation(shader, "translate"),0,-6,0)
	glDrawArrays(GL_POLYGON, 0, 4)
	# Objetos
	glUniform3f(glGetUniformLocation(shader, "cor"), 100/255, 0, 200/255)
	glUniform3f(glGetUniformLocation(shader, "escala"),1,1,1)
	glUniform3f(glGetUniformLocation(shader, "translate"),arvores[0][0],-2,arvores[0][1])
	glDrawArrays(GL_POLYGON, 0, 4)
	glUniform3f(glGetUniformLocation(shader, "translate"),arvores[1][0],-2,arvores[1][1])
	glDrawArrays(GL_POLYGON, 0, 4)
	glUniform3f(glGetUniformLocation(shader, "translate"),arvores[2][0],-2,arvores[2][1])
	glDrawArrays(GL_POLYGON, 0, 4)
	glUniform3f(glGetUniformLocation(shader, "translate"),arvores[3][0],-2,arvores[3][1])
	glDrawArrays(GL_POLYGON, 0, 4)
	glUniform3f(glGetUniformLocation(shader, "translate"),arvores[4][0],-2,arvores[4][1])
	glDrawArrays(GL_POLYGON, 0, 4)
	glUniform3f(glGetUniformLocation(shader, "translate"),arvores[5][0],-2,arvores[5][1])
	glDrawArrays(GL_POLYGON, 0, 4)
	glUniform3f(glGetUniformLocation(shader, "translate"),arvores[6][0],-2,arvores[6][1])
	glDrawArrays(GL_POLYGON, 0, 4)
	glUniform3f(glGetUniformLocation(shader, "translate"),arvores[7][0],-2,arvores[7][1])
	glDrawArrays(GL_POLYGON, 0, 4)
	glUniform3f(glGetUniformLocation(shader, "translate"),arvores[8][0],-2,arvores[8][1])
	glDrawArrays(GL_POLYGON, 0, 4)
	glUniform3f(glGetUniformLocation(shader, "translate"),arvores[9][0],-2,arvores[9][1])
	glDrawArrays(GL_POLYGON, 0, 4)
	glUniform3f(glGetUniformLocation(shader, "translate"),arvores[10][0],-2,arvores[10][1])
	glDrawArrays(GL_POLYGON, 0, 4)
	glUniform3f(glGetUniformLocation(shader, "translate"),arvores[11][0],-2,arvores[11][1])
	glDrawArrays(GL_POLYGON, 0, 4)
	glUniform3f(glGetUniformLocation(shader, "translate"),arvores[12][0],-2,arvores[12][1])
	glDrawArrays(GL_POLYGON, 0, 4)
	glUniform3f(glGetUniformLocation(shader, "translate"),arvores[13][0],-2,arvores[13][1])
	glDrawArrays(GL_POLYGON, 0, 4)
	glUniform3f(glGetUniformLocation(shader, "translate"),arvores[14][0],-2,arvores[14][1])
	glDrawArrays(GL_POLYGON, 0, 4)
	glUniform3f(glGetUniformLocation(shader, "translate"),arvores[15][0],-2,arvores[15][1])
	glDrawArrays(GL_POLYGON, 0, 4)
	glUniform3f(glGetUniformLocation(shader, "translate"),arvores[16][0],-2,arvores[16][1])
	glDrawArrays(GL_POLYGON, 0, 4)
	glUniform3f(glGetUniformLocation(shader, "translate"),arvores[17][0],-2,arvores[17][1])
	glDrawArrays(GL_POLYGON, 0, 4)
	glUniform3f(glGetUniformLocation(shader, "translate"),arvores[18][0],-2,arvores[18][1])
	glDrawArrays(GL_POLYGON, 0, 4)
	glUniform3f(glGetUniformLocation(shader, "translate"),arvores[19][0],-2,arvores[19][1])
	glDrawArrays(GL_POLYGON, 0, 4)
	# Personagem
	glUniform3f(glGetUniformLocation(shader, "cor"), 1, 1, 1)
	glUniform3f(glGetUniformLocation(shader, "translate"),-pos[0]-4*math.sin(-rotY*math.pi/180),-3,-pos[2]-4*math.cos(-rotY*math.pi/180))
	glUniform1f(glGetUniformLocation(shader, "Y"), -rotY*math.pi/180)
	glDrawArrays(GL_POLYGON, 0, 4)
	glBindFramebuffer(GL_FRAMEBUFFER, 0)
	# Cenario Mesmo
	view = pyrr.matrix44.create_perspective_projection_matrix(60, 5/4, .1, 1000)
	p = glGetUniformLocation(shader, "view")
	glUniformMatrix4fv(p, 1, GL_FALSE, view)
	glViewport(0, 0, 500, 400)
	glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
	# Filtro
	glUniform1i(glGetUniformLocation(shader, "filtro"), 0)
	# Gameplay
	glUniform1f(glGetUniformLocation(shader, "rX"), rotX*math.pi/180)
	glUniform1f(glGetUniformLocation(shader, "rY"), rotY*math.pi/180)
	glUniform3f(glGetUniformLocation(shader, "pos"), pos[0], pos[1], pos[2])
	# Cenario
	glUniform3f(glGetUniformLocation(shader, "cor"), 1, 0, 0)
	glUniform3f(glGetUniformLocation(shader, "escala"),2000,2000,1)
	glUniform3f(glGetUniformLocation(shader, "deform"),0,0,0)
	glUniform3f(glGetUniformLocation(shader, "translate"),0,-5,0)
	glUniform1f(glGetUniformLocation(shader, "X"), math.pi/2)
	glUniform1f(glGetUniformLocation(shader, "Y"), 0)
	glDrawArrays(GL_POLYGON, 0, 4)
	glUniform3f(glGetUniformLocation(shader, "translate"),0,-6,0)
	glDrawArrays(GL_POLYGON, 0, 4)
	# Objetos
	glUniform3f(glGetUniformLocation(shader, "cor"), 100/255, 0, 200/255)
	glUniform3f(glGetUniformLocation(shader, "escala"),1,1,1)
	glUniform3f(glGetUniformLocation(shader, "translate"),arvores[0][0],-2,arvores[0][1])
	glDrawArrays(GL_POLYGON, 0, 4)
	glUniform3f(glGetUniformLocation(shader, "translate"),arvores[1][0],-2,arvores[1][1])
	glDrawArrays(GL_POLYGON, 0, 4)
	glUniform3f(glGetUniformLocation(shader, "translate"),arvores[2][0],-2,arvores[2][1])
	glDrawArrays(GL_POLYGON, 0, 4)
	glUniform3f(glGetUniformLocation(shader, "translate"),arvores[3][0],-2,arvores[3][1])
	glDrawArrays(GL_POLYGON, 0, 4)
	glUniform3f(glGetUniformLocation(shader, "translate"),arvores[4][0],-2,arvores[4][1])
	glDrawArrays(GL_POLYGON, 0, 4)
	glUniform3f(glGetUniformLocation(shader, "translate"),arvores[5][0],-2,arvores[5][1])
	glDrawArrays(GL_POLYGON, 0, 4)
	glUniform3f(glGetUniformLocation(shader, "translate"),arvores[6][0],-2,arvores[6][1])
	glDrawArrays(GL_POLYGON, 0, 4)
	glUniform3f(glGetUniformLocation(shader, "translate"),arvores[7][0],-2,arvores[7][1])
	glDrawArrays(GL_POLYGON, 0, 4)
	glUniform3f(glGetUniformLocation(shader, "translate"),arvores[8][0],-2,arvores[8][1])
	glDrawArrays(GL_POLYGON, 0, 4)
	glUniform3f(glGetUniformLocation(shader, "translate"),arvores[9][0],-2,arvores[9][1])
	glDrawArrays(GL_POLYGON, 0, 4)
	glUniform3f(glGetUniformLocation(shader, "translate"),arvores[10][0],-2,arvores[10][1])
	glDrawArrays(GL_POLYGON, 0, 4)
	glUniform3f(glGetUniformLocation(shader, "translate"),arvores[11][0],-2,arvores[11][1])
	glDrawArrays(GL_POLYGON, 0, 4)
	glUniform3f(glGetUniformLocation(shader, "translate"),arvores[12][0],-2,arvores[12][1])
	glDrawArrays(GL_POLYGON, 0, 4)
	glUniform3f(glGetUniformLocation(shader, "translate"),arvores[13][0],-2,arvores[13][1])
	glDrawArrays(GL_POLYGON, 0, 4)
	glUniform3f(glGetUniformLocation(shader, "translate"),arvores[14][0],-2,arvores[14][1])
	glDrawArrays(GL_POLYGON, 0, 4)
	glUniform3f(glGetUniformLocation(shader, "translate"),arvores[15][0],-2,arvores[15][1])
	glDrawArrays(GL_POLYGON, 0, 4)
	glUniform3f(glGetUniformLocation(shader, "translate"),arvores[16][0],-2,arvores[16][1])
	glDrawArrays(GL_POLYGON, 0, 4)
	glUniform3f(glGetUniformLocation(shader, "translate"),arvores[17][0],-2,arvores[17][1])
	glDrawArrays(GL_POLYGON, 0, 4)
	glUniform3f(glGetUniformLocation(shader, "translate"),arvores[18][0],-2,arvores[18][1])
	glDrawArrays(GL_POLYGON, 0, 4)
	glUniform3f(glGetUniformLocation(shader, "translate"),arvores[19][0],-2,arvores[19][1])
	glDrawArrays(GL_POLYGON, 0, 4)
	# Personagem
	glUniform3f(glGetUniformLocation(shader, "cor"), 1, 1, 1)
	glUniform3f(glGetUniformLocation(shader, "translate"),-pos[0]-4*math.sin(-rotY*math.pi/180),-3,-pos[2]-4*math.cos(-rotY*math.pi/180))
	glUniform1f(glGetUniformLocation(shader, "Y"), -rotY*math.pi/180)
	glDrawArrays(GL_POLYGON, 0, 4)
	# Movimento
	temp1 = 3*(glfw.get_time()-tvec)
	if glfw.get_key(app, glfw.KEY_W):
		pos[0]+=math.sin(-rotY*math.pi/180)*temp1
		pos[2]+=math.cos(-rotY*math.pi/180)*temp1
	if glfw.get_key(app, glfw.KEY_A):
		pos[0]+=math.cos(-rotY*math.pi/180)*temp1
		pos[2]-=math.sin(-rotY*math.pi/180)*temp1
	if glfw.get_key(app, glfw.KEY_D):
		pos[0]-=math.cos(-rotY*math.pi/180)*temp1
		pos[2]+=math.sin(-rotY*math.pi/180)*temp1
	if glfw.get_key(app, glfw.KEY_S):
		pos[0]-=math.sin(-rotY*math.pi/180)*temp1
		pos[2]-=math.cos(-rotY*math.pi/180)*temp1
	if glfw.get_key(app, glfw.KEY_SPACE) and pos[1] == 0:
		pos[1]-=10
	if pos[1] < 0:
		pos[1]+=(glfw.get_time()-tvec)*10
	if pos[1] > 0:
		pos[1] = 0
	tvec = glfw.get_time()
	mouse = glfw.get_cursor_pos(app)
	glfw.set_cursor_pos(app, 250, 200)
	rotY-= 250-mouse[0]
	rotX-= 200-mouse[1]
	if rotX < -45:
		rotX = -45
	if rotX > 45:
		rotX = 45
	if rotY < 0:
		rotY+=360
	if rotY > 360:
		rotY-=360
	# FPS
	fps+=1
	if glfw.get_time() - tfps > 1:
		print("FPS : ",fps)
		tfps = glfw.get_time()
		fps = 0
	if glfw.get_key(app, glfw.KEY_P):
		glfw.destroy_window(app)
		break

glfw.terminate()



