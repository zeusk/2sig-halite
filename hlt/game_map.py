from . import entity


class Map:
    """
    Map which houses the current game information/metadata.
    
    :ivar my_id: Current player id associated with the map
    :ivar width: Map width
    :ivar height: Map height
    """

    def __init__(self, my_id, width, height):
        """
        :param my_id: User's id (tag)
        :param width: Map width
        :param height: Map height
        """
        self.my_id = my_id
        self.width = width
        self.height = height
        self._players = {}
        self._planets = {}

    def get_me(self):
        """
        :return: The user's player
        :rtype: Player
        """
        return self._players.get(self.my_id)

    def get_player(self, player_id):
        """
        :param int player_id: The id of the desired player
        :return: The player associated with player_id
        :rtype: Player
        """
        return self._players.get(player_id)

    def all_players(self):
        """
        :return: List of all players
        :rtype: list[Player]
        """
        return list(self._players.values())

    def get_planet(self, planet_id):
        """
        :param int planet_id:
        :return: The planet associated with planet_id
        :rtype: entity.Planet
        """
        return self._planets.get(planet_id)

    def all_planets(self):
        """
        :return: List of all planets
        :rtype: list[entity.Planet]
        """
        return list(self._planets.values())

    def _link(self):
        """
        Updates all the entities with the correct ship and planet objects

        :return:
        """
        for celestial_object in self.all_planets() + self.all_ships():
            celestial_object._link(self._players, self._planets)

    def _parse(self, map_string):
        """
        Parse the map description from the game.

        :param map_string: The string which the Halite engine outputs
        :return: nothing
        """
        tokens = map_string.split()

        self._players, tokens = Player._parse(tokens)
        self._planets, tokens = entity.Planet._parse(tokens)

        assert(len(tokens) == 0)  # There should be no remaining tokens at this point
        self._link()

    def all_ships(self):
        """
        Helper function to extract all ships from all players

        :return: List of ships
        :rtype: List[Ship]
        """
        all_ships = []
        for player in self.all_players():
            all_ships.extend(player.all_ships())
        return all_ships

    def all_uships(self):
        return [s for s in self.all_ships() if s.can_atk()]

    def all_dships(self):
        return [s for s in self.all_ships() if not s.can_atk()]

    def my_ships(self):
        return self.get_me().all_ships()

    def my_uships(self):
        return [s for s in self.my_ships() if s.can_atk()]

    def my_dships(self):
        return [s for s in self.my_ships() if not s.can_atk()]

    def en_ships(self):
        ships = []
        for player in self.all_players():
            if player != self.get_me():
                ships = ships + player.all_ships()
        return ships

    def en_uships(self):
        return [s for s in self.en_ships() if s.can_atk()]

    def en_dships(self):
        return [s for s in self.en_ships() if not s.can_atk()]

    def my_planets(self):
        return [p for p in self.all_planets() if p.owner == self.get_me()]

    def my_uplanets(self):
        return [p for p in self.my_planets() if not p.is_full()]

    def unowned_planets(self):
        return [p for p in self.all_planets() if not p.is_owned()]

    def en_planets(self):
        return [p for p in self.all_planets() if p.owner != self.get_me() and p.is_owned()]

    def all_entities(self):
        return self.all_ships() + self.all_planets()

    def remove_ship(self, ship):
        ship.owner.remove_ship(ship)

    def is_en(self, e):
        return e.owner != self.get_me()

    def contains_pt(self, p):
        return not(p.x < 0 or p.x > self.width or p.y < 0 or p.y > self.height)


class Player:
    """
    :ivar id: The player's unique id
    """
    def __init__(self, player_id, ships={}):
        """
        :param player_id: User's id
        :param ships: Ships user controls (optional)
        """
        self.id = player_id
        self._ships = ships #Dict

    def all_ships(self):
        """
        :return: A list of all ships which belong to the user
        :rtype: list[entity.Ship]
        """
        return list(self._ships.values())

    def get_ship(self, ship_id):
        """
        :param int ship_id: The ship id of the desired ship.
        :return: The ship designated by ship_id belonging to this user.
        :rtype: entity.Ship
        """
        return self._ships.get(ship_id)

    def remove_ship(self, ship):
        if ship in self._ships:
            del self._ships[ship]

    @staticmethod
    def _parse_single(tokens):
        """
        Parse one user given an input string from the Halite engine.

        :param list[str] tokens: The input string as a list of str from the Halite engine.
        :return: The parsed player id, player object, and remaining tokens
        :rtype: (int, Player, list[str])
        """
        player_id, *remainder = tokens
        player_id = int(player_id)
        ships, remainder = entity.Ship._parse(player_id, remainder)
        player = Player(player_id, ships)
        return player_id, player, remainder

    @staticmethod
    def _parse(tokens):
        """
        Parse an entire user input string from the Halite engine for all users.

        :param list[str] tokens: The input string as a list of str from the Halite engine.
        :return: The parsed players in the form of player dict, and remaining tokens
        :rtype: (dict, list[str])
        """
        num_players, *remainder = tokens
        num_players = int(num_players)
        players = {}

        for _ in range(num_players):
            player, players[player], remainder = Player._parse_single(remainder)

        return players, remainder

    def __str__(self):
        return "Player {} with ships {}".format(self.id, self.all_ships())

    def __repr__(self):
        return self.__str__()
