# ShadowMappingImprovisado
    Eu estava tentando fazer Shadow Mapping utilizando Python, Modern OpenGL e GLFW, especificamente um sistema que lembra-se o ciclo de dia e noite do sol, é bem simples mas ainda sim funciona como esperado, na primeira versão eu apenas fiz a sombra com uma posição fixa e direção fixa, vindo de cima no angulo de 90 graus para baixo que seria math.pi/2, mas depois eu quis ver se conseguiria mover a sombra como se estivesse num ciclo criado pela luz do dia e consegui.
    
    Depois para melhorar a qualidade da sombra por que originalmente o framebuffer tinha o exato tamanho da janela, eu alterei ele de forma que o framebuffer seja 8 vezes maior que a janela e o glViewport garante isso fazendo com que a sombra tenha uma qualidade maior sendo impressa.
