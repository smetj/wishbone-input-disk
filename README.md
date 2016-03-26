              __       __    __
    .--.--.--|__.-----|  |--|  |--.-----.-----.-----.
    |  |  |  |  |__ --|     |  _  |  _  |     |  -__|
    |________|__|_____|__|__|_____|_____|__|__|_____|
                                       version 2.1.2

    Build composable event pipeline servers with minimal effort.


    ===================
    wishbone.input.disk
    ===================

    Version: 0.1.0

    Reads messages from a disk buffer.
    ----------------------------------



        Parameters:

            - directory(str)
               |  The directory to write data to.

            - idle_trigger(bool)(False)
               |  When True, only reads events when no new events
               |  have been written to disk for at least <idle_time>.


            - idle_time(int)(10)
               |  The time in seconds required that no new events
               |  have been written to disk prior to start to consume
               |  the buffered data.


        Queues:

            - outbox
               |  Incoming events.

