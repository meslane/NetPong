~== GAMEPLAY ==~
    160 (x) by 90 (y) playfield
    
~== CURRENT BUGS ==~
    -Netcode is extremely shitty
        -Users frequenty desync because of all the separate threads
        -Gets slower to respond over time
        -Should move all netcode into one thread

        -Improved on server side by using select module
        -Need to fix client
        -Problem is that server is so much faster, it's overwhelming the client with packets
        -Keep track of last sent packet and have a timer of some sort

    -Server has a memory leak after implementing non blocking sockets
        -Seems to happen after closing the first connection
        -Fixed by adding exception handling