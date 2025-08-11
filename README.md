Bunny Brave

Bunny Brave é um jogo de plataforma 2D desenvolvido em Python com a biblioteca PgZero. O objetivo é ajudar um coelho corajoso a sobreviver, coletando moedas para pontos e cenouras para um poder de invencibilidade, enquanto enfrenta inimigos perigosos. O desafio final é lutar contra o temível chefão do Sol para alcançar a vitória.
🕹️ Recursos do Jogo

    Mecânica de Plataforma: O coelho pode andar, pular e interagir com diferentes plataformas.

    Inimigos Variados: Enfrente inimigos terrestres (Spikeman) e voadores (Flyman) que patrulham a área.

    Ataque e Defesa: Use uma rede para capturar os inimigos e ative um escudo de invencibilidade após coletar um número suficiente de cenouras.

    Luta contra o Chefão: O jogo transiciona para uma batalha final contra um chefão com ataques especiais e múltiplos pontos de vida.

    Sistema de Pontuação e Vidas: Colete diferentes tipos de moedas para aumentar a sua pontuação e gerencie suas três vidas.

    Controle de Áudio: Música de fundo e efeitos sonoros para uma experiência imersiva, com um botão para silenciar o jogo a qualquer momento.

    Interface Intuitiva (HUD): A tela exibe informações importantes como vidas, pontuação, tempo e o progresso do power-up de invencibilidade.

🎮 Como Jogar

Objetivo: Sobreviva aos inimigos, colete itens e derrote o chefão do Sol.

Controles:

    Setas Esquerda/Direita: Movem o coelho.

    Seta para Cima: Faz o coelho pular.

    ESPAÇO: Inicia o ataque com a rede.

    Clique do Mouse: Liga ou desliga o áudio no botão de mudo.

    ENTER: Seleciona opções no menu e reinicia o jogo nas telas de Game Over e Vitória.

    BACKSPACE: Retorna ao menu principal a partir da tela de instruções.

⚙️ Requisitos e Instalação

O jogo foi desenvolvido usando a biblioteca PgZero, que simplifica a criação de jogos com o Pygame. Para rodar o projeto, você precisará ter o Python 3 e o PgZero instalados.

    Instale o PgZero:

    pip install pgzero

    Execute o jogo:
    Salve o código como bunny_brave.py (ou o nome que preferir) e execute-o a partir do terminal na mesma pasta:

    pgzrun bunny_brave.py

👨‍💻 Estrutura do Código

O código é bem organizado em seções para facilitar a leitura e manutenção:

    Variáveis Globais: Define as constantes do jogo, estados e listas de entidades.

    Classes: Cada tipo de objeto do jogo (Player, Enemy, Boss, Coin, Platform, etc.) tem sua própria classe, facilitando a organização da lógica e das propriedades.

    Funções de Lógica (setup, spawn, reset): Preparam o ambiente do jogo e gerenciam a criação de elementos.

    Loop Principal (draw e update): As funções principais do PgZero que controlam a renderização visual e a lógica do jogo a cada quadro.
