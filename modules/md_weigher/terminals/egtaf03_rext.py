from modules.md_weigher.terminals.egtaf03 import EgtAf03

class EgtAf03Rext(EgtAf03):
	def __init__(self, self_config, max_weight, min_weight, division, maintaine_session_realtime_after_command, diagnostic_has_priority_than_realtime, always_execute_realtime_in_undeground, need_take_of_weight_before_weighing, need_take_of_weight_on_startup, continuous_transmission, node, terminal, run):
		# Chiama il costruttore della classe base
		super().__init__(self_config, max_weight, min_weight, division, maintaine_session_realtime_after_command, diagnostic_has_priority_than_realtime, always_execute_realtime_in_undeground, need_take_of_weight_before_weighing, need_take_of_weight_on_startup, continuous_transmission, node, terminal, run)
		self.realtime_action = "REXT"