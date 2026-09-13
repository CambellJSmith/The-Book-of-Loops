CREATE TABLE `cards` (
	`id` text PRIMARY KEY NOT NULL,
	`species_id` text NOT NULL,
	`payload` text NOT NULL,
	`revision` integer DEFAULT 1 NOT NULL,
	`created_at` integer NOT NULL,
	`updated_at` integer NOT NULL
);
--> statement-breakpoint
CREATE UNIQUE INDEX `idx_cards_species_id` ON `cards` (`species_id`);--> statement-breakpoint
CREATE INDEX `idx_cards_updated_at` ON `cards` (`updated_at`);