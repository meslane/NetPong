~== GAMEPLAY ==~
    160 (x) by 90 (y) playfield
    
~== CURRENT BUGS ==~
    -Netcode is extremely shitty
        -Users frequenty desync because of all the separate threads
        -Gets slower to respond over time
        -Should move all netcode into one thread

    -Server has a memory leak after implementing non blocking sockets
        -Seems to happen after closing the first connection
        -Fixed by adding exception handling