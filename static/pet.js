// Teddy Bear Pet — Sprite Animation Engine
// Spritesheet: 8 cols × 9 rows, each cell 192×208 px, total 1536×1872 px
const COLS = 8;
const CELL_W = 192;
const CELL_H = 208;
const SPRITE_URL = '/static/pet/spritesheet.webp';

const ANIMATIONS = {
    idle:    { row: 0, frames: 6, interval: 200 },
    waiting: { row: 6, frames: 6, interval: 180 },
    review:  { row: 8, frames: 6, interval: 160 },
    waving:  { row: 3, frames: 4, interval: 150 },
    failed:  { row: 5, frames: 8, interval: 140 },
};

class Pet {
    constructor(el) {
        this.el = el;
        this.state = 'idle';
        this.frame = 0;
        this.timer = null;
        this._locked = null; // temporary state lock
        el.style.backgroundImage = `url(${SPRITE_URL})`;
        el.style.backgroundSize = `${COLS * 100}% auto`;
        el.style.backgroundRepeat = 'no-repeat';
        this._render();
        this._start();
    }

    setState(state) {
        if (this._locked) return;
        if (!ANIMATIONS[state]) return;
        if (this.state === state) return;
        this.state = state;
        this.frame = 0;
        this._render();
        this._start();
    }

    /** Temporarily override state, then return to base after duration (ms) */
    play(state, duration) {
        if (!ANIMATIONS[state]) return;
        this._locked = state;
        this.state = state;
        this.frame = 0;
        this._render();
        clearTimeout(this._lockTimer);
        this._lockTimer = setTimeout(() => {
            this._locked = null;
            this.setState('idle');
        }, duration);
    }

    _start() {
        this._stop();
        this.timer = setInterval(() => this._tick(), this._interval());
    }

    _stop() {
        if (this.timer) { clearInterval(this.timer); this.timer = null; }
    }

    _interval() {
        return ANIMATIONS[this.state]?.interval || 200;
    }

    _tick() {
        const anim = ANIMATIONS[this.state];
        if (!anim) return;
        this.frame = (this.frame + 1) % anim.frames;
        this._render();
    }

    _render() {
        const anim = ANIMATIONS[this.state];
        if (!anim) return;
        const col = this.frame;
        const row = anim.row;
        this.el.style.backgroundPosition = `${col * (100 / (COLS - 1))}% ${row * (100 / 8)}%`;
    }
}

// Global pet instance — set up after DOM ready
document.addEventListener('DOMContentLoaded', () => {
    const el = document.getElementById('petAvatar');
    if (el) {
        window.pet = new Pet(el);
    }
});
