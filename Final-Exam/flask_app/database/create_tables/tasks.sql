CREATE TABLE IF NOT EXISTS `tasks` (
`task_id`      int(11)        NOT NULL AUTO_INCREMENT 	COMMENT 'the current task made',
`board_id`     int(11)        NOT NULL                	COMMENT 'FK: the board the task is part of', 
`description`  varchar(1000)  NOT NULL                	COMMENT 'the description of the task',
`category`     varchar(100)   NOT NULL            	    COMMENT 'either Todo, Doing, or Completed',
PRIMARY KEY  (`task_id`),
FOREIGN KEY (board_id) REFERENCES boards(board_id)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COMMENT="Tasks for project";