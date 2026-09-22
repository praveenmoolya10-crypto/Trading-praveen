from dataclasses import dataclass
from datetime import datetime
@dataclass
class Candle:
 symbol:str; market:str; timestamp:datetime; open:float; high:float; low:float; close:float; volume:float=0
@dataclass
class Order:
 id:str; symbol:str; market:str; side:str; quantity:float; order_type:str; status:str; filled_quantity:float=0; average_price:float|None=None; broker_order_id:str|None=None
