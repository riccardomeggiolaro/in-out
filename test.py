# Modello per la tabella User
class User(Base):
	__tablename__ = 'user'
	id = Column(Integer, primary_key=True, index=True)
	username = Column(String)
	password = Column(String)
	level = Column(Integer)
	description = Column(String)
	printer_name = Column(String, nullable=True)

# Modello per la tabella Vehicle
class Vehicle(Base):
	__tablename__ = 'vehicle'
	id = Column(Integer, primary_key=True, index=True)
	name = Column(String)
	plate = Column(String)
	reservations = relationship("Reservation", back_populates="vehicle", cascade="all, delete")

class SocialReason(Base):
	__tablename__ = 'social_reason'
	id = Column(Integer, primary_key=True, index=True)
	name = Column(String)
	cell = Column(String)
	cfpiva = Column(String)
	# Relazioni specifiche con foreign_keys specificati
	customer_reservations = relationship("Reservation", 
										foreign_keys="Reservation.idCustomer", 
										back_populates="customer", 
										cascade="all, delete")
	supplier_reservations = relationship("Reservation", 
										foreign_keys="Reservation.idSupplier", 
										back_populates="supplier", 
										cascade="all, delete")
# Modello per la tabella Material
class Material(Base):
	__tablename__ = 'material'
	id = Column(Integer, primary_key=True, index=True) 
	name = Column(String, index=True)
	reservations = relationship("Reservation", back_populates="material", cascade="all, delete")

class Reservation(Base):
	__tablename__ = 'reservation'
	id = Column(Integer, primary_key=True, index=True)
	idCustomer = Column(Integer, ForeignKey('social_reason.id'))
	idSupplier = Column(Integer, ForeignKey('social_reason.id'))
	idVehicle = Column(Integer, ForeignKey('vehicle.id'))
	idMaterial = Column(Integer, ForeignKey('material.id'))
	number_weighings = Column(Integer, default=0, nullable=False)
	date_created = Column(DateTime, default=datetime.utcnow)
	note = Column(String)
	selected = Column(Boolean, index=True, default=False)
	
	# Relazioni
	customer = relationship("SocialReason", 
						   foreign_keys=[idCustomer], 
						   back_populates="customer_reservations")
	supplier = relationship("SocialReason", 
						   foreign_keys=[idSupplier], 
						   back_populates="supplier_reservations")
	vehicle = relationship("Vehicle", back_populates="reservations")
	material = relationship("Material", back_populates="reservations")
	weighings = relationship("Weighing", back_populates="reservation", cascade="all, delete")

# Modello per la tabella Weighing
class Weighing(Base):
	__tablename__ = 'weighing'
	id = Column(Integer, primary_key=True, index=True, nullable=False)
	weight = Column(Integer, nullable=True)
	date = Column(DateTime, nullable=True)
	pid = Column(String, nullable=True)
	weigher = Column(String, nullable=True)
	idReservation = Column(Integer, ForeignKey('reservation.id'), nullable=False)
	
	# Relazioni
	reservation = relationship("Reservation", back_populates="weighings")

# Dizionario di modelli per mappare nomi di tabella a classi di modelli
table_models = {
	'vehicle': Vehicle,
	'social_reason': SocialReason,
	'material': Material,
	'reservation': Reservation,
 	'weighing': Weighing,
	'user': User
}
def filter_data(table_name, filters=None, limit=None, offset=None):
	"""Esegue una ricerca filtrata su una tabella specifica con supporto per la paginazione
	e popola automaticamente le colonne di riferimenti con i dati delle tabelle correlate.

	Args:
		table_name (str): Il nome della tabella su cui eseguire la ricerca.
		filters (dict): Dizionario di filtri (nome_colonna: valore) per la ricerca. Default è None.
		limit (int): Numero massimo di righe da visualizzare. Default è None.
		offset (int): Numero di righe da saltare. Default è None.

	Returns:
		tuple: Una tupla contenente:
			- una lista di dizionari contenenti i risultati della ricerca,
			- il numero totale di righe nella tabella.
	"""

	# Verifica che il modello esista nel dizionario dei modelli
	model = table_models.get(table_name.lower())
	if not model:
		raise ValueError(f"Tabella '{table_name}' non trovata.")

	# Crea una sessione e costruisce la query
	session = SessionLocal()
	try:
		# Inizia la query sulla tabella specificata
		query = session.query(model)

		import libs.lb_log as lb_log

		# Aggiungi il caricamento delle relazioni per i campi che sono referenze (foreign key)
		for relationship_name, relationship_obj in model.__mapper__.relationships.items():
			lb_log.warning("sss")
			# Verifica se la relazione esiste
			if relationship_obj:
				query = query.options(joinedload(relationship_obj))

		# Aggiungi i filtri, se specificati
		if filters:
			for column, value in filters.items():
				if hasattr(model, column):
					if type(value) == str:
						query = query.filter(getattr(model, column).like(f'%{value}%'))
					elif type(value) == int:
						query = query.filter(getattr(model, column) == value)
					elif value is None:
						query = query.filter(getattr(model, column).is_(None))
					else:
						raise ValueError(f"Operatore di ricerca '{value[0]}' non supportato.")
				else:
					raise ValueError(f"Colonna '{column}' non trovata nella tabella '{table_name}'.")

		# Esegui una query separata per ottenere il numero totale di righe
		total_rows = query.count()

		# Applica la paginazione se limit e offset sono specificati
		if limit is not None:
			query = query.limit(limit)
		if offset is not None:
			query = query.offset(offset)

		# Esegui la query per ottenere i risultati filtrati
		results = query.all()

		session.close()

		# Converte i risultati in una lista di dizionari
		result_list = [
			{column.name: getattr(record, column.name) for column in model.__table__.columns}
			for record in results
		]
		
		return result_list, total_rows

	except Exception as e:
		session.close()
		raise e