# src/logic/registry.py
from src.logic.villains.base_villain import BaseVillainLogic
from src.logic.villains.red_skull import RedSkullLogic
from src.logic.villains.taskmaster import TaskmasterLogic
from src.logic.villains.ultron import UltronLogic
from src.logic.villains.baron_zemo import ZemoLogic
from src.logic.villains.kang import KangLogic
from src.logic.villains.loki import LokiLogic
from src.logic.villains.hela import HelaLogic
from src.logic.villains.black_dwarf import BlackDwarfLogic
from src.logic.villains.ebony_maw import EbonyMawLogic
from src.logic.villains.proxima_midnight import ProximaMidnightLogic
from src.logic.villains.ronan import RonanLogic
from src.logic.villains.rhino import RhinoLogic
from src.logic.villains.thanos import ThanosLogic
from src.logic.villains.modok import ModokLogic
from src.logic.villains.venom import VenomLogic
from src.logic.villains.carnage import CarnageLogic
from src.logic.villains.killmonger import KillmongerLogic
from src.logic.villains.dormammu import DormammuLogic
from src.logic.villains.corvus_glaive import CorvusGlaiveLogic
from src.logic.villains.mysterio import MysterioLogic
from src.logic.villains.doctor_octopus import DoctorOctopusLogic
from src.logic.villains.kraven import KravenLogic
from src.logic.villains.green_goblin import GreenGoblinLogic
from src.logic.villains.electro import ElectroLogic
from src.logic.villains.sandman import SandmanLogic
from src.logic.villains.vulture import VultureLogic
from src.logic.villains.kingpin import KingpinLogic
from src.logic.villains.bullseye import BullseyeLogic
from src.logic.villains.sinister_six import SinisterSixLogic


# Map internal_id to the Logic Class
_LOGIC_MAP = {
    "red_skull": RedSkullLogic,
    "taskmaster": TaskmasterLogic,
    "ultron": UltronLogic,
    "baron_zemo": ZemoLogic,
    "kang": KangLogic,
    "loki": LokiLogic,
    "hela": HelaLogic,
    "black_dwarf": BlackDwarfLogic,
    "ebony_maw": EbonyMawLogic,
    "proxima_midnight": ProximaMidnightLogic,
    "ronan": RonanLogic,
    "rhino": RhinoLogic,
    "thanos": ThanosLogic,
    "modok": ModokLogic,
    "venom": VenomLogic,
    "carnage": CarnageLogic,
    "killmonger": KillmongerLogic,
    "dormammu": DormammuLogic,
    "corvus_glaive": CorvusGlaiveLogic,
    "mysterio": MysterioLogic,
    "doctor_octopus": DoctorOctopusLogic,
    "kraven": KravenLogic,
    "green_goblin": GreenGoblinLogic,
    "electro": ElectroLogic,
    "sandman": SandmanLogic,
    "vulture": VultureLogic,
    "kingpin": KingpinLogic,
    "bullseye": BullseyeLogic,
    "sinister_six": SinisterSixLogic,
    #"ultron": UltronLogic,
}

def get_villain_logic(internal_id):
    # Return RedSkullLogic if id matches, otherwise use the Default Base
    return _LOGIC_MAP.get(internal_id, BaseVillainLogic)
    
def get_hero_logic(internal_id):
    """
    🚨 THE NEW BRIDGE: Connects actors to the SpecialAbilitySystem 
    without causing circular import loops.
    """
    from src.systems.special_abilities import SpecialAbilitySystem
    return SpecialAbilitySystem.HERO_LOGIC_MAP.get(internal_id)