CREATE TABLE IF NOT EXISTS `contributors` (
`contributor_id`  int(11)      NOT NULL auto_increment	  COMMENT 'the id of contributor to a project',
`board_id`        int(11)      NOT NULL                   COMMENT 'FK: the board id',
`user_email`      varchar(100) NOT NULL                   COMMENT 'email of users for this board',
`role`            varchar(100) NOT NULL                   COMMENT 'role of user for this board',
PRIMARY KEY (`contributor_id`),
FOREIGN KEY (board_id) REFERENCES boards(board_id)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COMMENT="Boards made by users";