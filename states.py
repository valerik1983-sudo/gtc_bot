from aiogram.fsm.state import State
from aiogram.fsm.state import StatesGroup


# =========================
# Регистрация
# =========================

class Registration(StatesGroup):

    fio = State()

    birth_date = State()

    phone = State()

    city = State()

    gender = State()

    is_partner = State() 

    confirm_not_registered = State()


# =========================
# Консультация
# =========================

class Consultation(StatesGroup):
    confirm_data = State()
    edit_data = State()
    waiting_fio = State()
    waiting_phone = State()
    waiting_city = State()
    topic = State()      # ← должно быть
    phone = State()
    preferred_time = State()

class MentorMessage(StatesGroup):

    waiting_text = State()    


class ClientReply(StatesGroup):

    waiting_text = State()    

class Broadcast(StatesGroup):

    waiting_message = State()    

class AdminComplaintReply(StatesGroup):

    waiting_text = State()    

class OrderCheckout(StatesGroup):
    confirm_data = State()      # подтверждение данных
    city = State()              # город
    delivery_method = State()   # способ доставки
    pickup_point = State()      # пункт выдачи
    final_confirm = State()     # итоговое подтверждение    

class Quiz(StatesGroup):
    q1 = State()  # сумма
    q2 = State()  # что бы сделали
    q3 = State()  # время
    q4 = State()  # что ближе
    q5 = State()  # рекомендации
    q6 = State()  # беспокоит    

class AdminStates(StatesGroup):
    waiting_order_answer = State()    
    
class ReplyState(StatesGroup):
    waiting_for_reply = State()
    waiting_user_reply = State()    
    
# states.py - добавить в конец файла

class Diagnostics(StatesGroup):
    """Состояния для диагностики"""
    waiting_question = State()    
    
class PromotionEdit(StatesGroup):
    waiting_title = State()
    waiting_description = State()
    waiting_photo = State()
    waiting_link = State()
    waiting_expires = State()
    waiting_confirm_delete = State()   
    
class InviteState(StatesGroup):
    waiting_source = State()    
    
class CustomSource(StatesGroup):
    waiting_source = State()    

class AdminKnowledge(StatesGroup):
    waiting_product_name = State()
    waiting_product_description = State()
    waiting_rule_text = State()    