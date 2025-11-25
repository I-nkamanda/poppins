CREATE TABLE `Result` (
	`Key`	VARCHAR(255)	NOT NULL,
	`id`	NOT NULL	NOT NULL,
	`question_ids`	NOT NULL	NULL,
	`num_of_answer`	not null	NULL,
	`Field`	VARCHAR(255)	NULL
);

CREATE TABLE `Exercise` (
	`NAME`	NOT NULL	NOT NULL,
	`chapter_id`	NOT NULL	NOT NULL,
	`course_id`	NOT NULL	NOT NULL,
	`Key2`	VARCHAR(255)	NOT NULL,
	`is_complete`	VARCHAR(255)	NULL,
	`subject_md`	not null	NULL,
	`Field`	VARCHAR(255)	NULL
);

CREATE TABLE `Concept` (
	`INT`	NOT NULL	NOT NULL,
	`chapter_id`	NOT NULL	NOT NULL,
	`course_id`	NOT NULL	NOT NULL,
	`Key2`	VARCHAR(255)	NOT NULL,
	`is_complete`	VARCHAR(255)	NULL,
	`description`	VARCHAR(255)	NULL,
	`body`	NOT NULL	NULL
);

CREATE TABLE `Course` (
	`id`	NOT NULL	NOT NULL,
	`member_id`	VARCHAR(255)	NOT NULL,
	`created_at`	NOT NULL	NULL,
	`edited_at`	NULL	NULL,
	`deleted_at`	NULL	NULL,
	`title`	NOT NULL	NULL,
	`description`	NOT NULL	NULL,
	`prompt`	NOT NULL	NULL,
	`maxChapters`	NOT NULL	NULL,
	`external_link`	NOT NULL	NULL,
	`difficulty`	NOT NULL	NULL
);

CREATE TABLE `Member` (
	`id`	NOT NULL	NOT NULL,
	`email`	NOT NULL	NULL,
	`password`	NULL	NULL,
	`created_at`	NOT NULL	NULL,
	`edited_at`	NOT NULL	NULL,
	`deleted_at`	NULL	NULL,
	`nickname`	NULL	NULL,
	`Field`	VARCHAR(255)	NULL
);

CREATE TABLE `Quiz` (
	`id`	NOT NULL	NOT NULL,
	`id2`	NOT NULL	NOT NULL,
	`id3`	NOT NULL	NOT NULL,
	`Key`	VARCHAR(255)	NOT NULL,
	`question_type`	VARCHAR(255)	NULL,
	`title`	not null	NULL,
	`Field`	VARCHAR(255)	NOT NULL,
	`Field2`	VARCHAR(255)	NOT NULL
);

CREATE TABLE `chapter` (
	`id`	NOT NULL	NOT NULL,
	`course_id`	NOT NULL	NOT NULL,
	`member_id`	NOT NULL	NOT NULL,
	`created_at`	NOT NULL	NULL,
	`edited_at`	NULL	NULL,
	`deleted_at`	NULL	NULL,
	`description`	VARCHAR(255)	NULL,
	`is_created`	VARCHAR(255)	NULL,
	`is_studying`	VARCHAR(255)	NULL,
	`index`	VARCHAR(255)	NULL,
	`Field`	VARCHAR(255)	NULL
);

