from Telemetry import Telemetry
from Launch import Launch

# 1. cria a prancheta compartilhada
telemetry = Telemetry()

# 2. cria e executa o lançamento
launch = Launch(telemetry)
launch.run()

# 3. imprime o log de eventos
telemetry.print_log()