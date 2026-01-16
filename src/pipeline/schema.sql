CREATE TABLE IF NOT EXISTS puzzles (
    puzzle_id       BIGINT PRIMARY KEY,
    puzzle_date     DATE UNIQUE NOT NULL,

    width           INT,
    height          INT,
    cell_count      INT,
    black_count     INT,

    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS clue_answers (
    puzzle_id       BIGINT NOT NULL REFERENCES puzzles(puzzle_id) ON DELETE CASCADE,
    clue_id         INT NOT NULL,
    direction       TEXT NOT NULL,
    label           TEXT NOT NULL,
    clue_text       TEXT NOT NULL,
    answer_display  TEXT NOT NULL,
    answer_canonical TEXT NOT NULL,
    answer_length   INT NOT NULL,
    has_rebus       BOOLEAN NOT NULL,

    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    PRIMARY KEY (puzzle_id, clue_id)
);

CREATE TABLE IF NOT EXISTS solve_times (
    puzzle_id           BIGINT PRIMARY KEY REFERENCES puzzles(puzzle_id) ON DELETE CASCADE,
    puzzle_date         DATE NOT NULL,
    seconds_spent_solving   INT,
    solved              BOOLEAN,
    percent_filled      DOUBLE PRECISION,

    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_clue_answers_date
    ON clue_answers (puzzle_id);

CREATE INDEX IF NOT EXISTS idx_solve_times_date
    ON solve_times (puzzle_date);

