class NeyboyChallenge {

	constructor(ctx, el, width=180, height=320, fullscreen_mode=5) {
		this.ctx = ctx;

		if (ctx.data) {
			this.data = ctx.data;
			this.data.project[10] = width;
			this.data.project[11] = height;
			// 0 = off, 1 = crop, 2 = scale inner, 3 = scale outer, 4 = letterbox scale, 5 = integer letterbox scale
			this.data.project[12] = fullscreen_mode; 
			// this.audio_to_preload = pm[7];
			this.data.project[7] = []
			// this.preloadSounds = pm[25];
			this.data.project[25] = false;			
		    // this.data.project[15] = false;
		}

		this.runtime = ctx.cr_getC2Runtime();
		if (!this.runtime) {
			this.runtime = ctx.cr_createRuntime(el);	
		}
		// setInterval(()=>{
		// 		console.log(this.dimensions());
		// }, 1000)
	}

	isReady(){
		let touchToStartText = this.runtime.getObjectByUID(6);
		if (touchToStartText)
			return touchToStartText.visible;
		else
			return false;
	}

	isOver(){
		let replayButton = this.runtime.getObjectByUID(16);
		if (replayButton && replayButton.behavior_insts)
			return replayButton.behavior_insts[0].useCurrent;
		else
			return false;
	}

	isReplayButtonActive() {
        return this.isOver();
	}

	shuffleToasts() {
		let anim = this.runtime.getObjectByUID(26);
		if (anim) {
            let frames = anim.cur_animation.frames;
            anim.cur_animation.frames = frames.map((a) => [Math.random(),a]).sort((a,b) => a[0]-b[0]).map((a) => a[1]);
        }
	}

	pause() {
        this.ctx.cr_setSuspended(true);
        return this;
	}

	resume() {
        this.ctx.cr_setSuspended(false);
        return this;
	}

	getScore() {
		const scoreInstance = this.runtime.getObjectByUID(5); 
        const score = scoreInstance.text || '0';
        return parseInt(score, 10);			
	}

	getPosition() {
		const positionInstance = this.runtime.getObjectByUID(0); 
        let angle = positionInstance.angle;
        // convert angle to [-1, 1] range 
        if (angle < 6.5 && angle >= 4.5)
            angle = Math.max((angle - 6.3) / 1.5, -1);
        else if (angle < 1.8 && angle > 0)
            angle = Math.min(angle / 1.5, 1);
        const position = {
            name: positionInstance.animTriggerName,
            angle: angle
        }; 
        return position;			
	}

	dimensions() {
        let {x, y, width, height} = this.runtime.canvas.getBoundingClientRect();

        x = x || 0;
		y = y || 0;
        
        return {x, y, width, height};			
	}

	status(){
        return this.runtime.getEventVariableByName('isPlaying').data;
	}

	async state(includeSnapshot=true, format='image/jpeg', quality=30) {
        return new Promise((resolve, reject) => {
            const dimensions = this.dimensions();
            const score = this.getScore();
            const hiscore = this.runtime.getEventVariableByName('hiscore').data || 0;
            const position = this.getPosition();
            const status = this.status();
            if (includeSnapshot) {
                this.ctx['cr_onSnapshot'] = function(snapshot) {
                    resolve({score, hiscore, snapshot, status, dimensions, position});
                };
                this.ctx.cr_getSnapshot(format, quality);
            } else {
                const snapshot = null;
                resolve({score, hiscore, snapshot, status, dimensions, position});
            }
        })
    }			
}


function getParameterByName(name, url) {
    if (!url) url = window.location.href;
    name = name.replace(/[\[\]]/g, '\\$&');
    var regex = new RegExp('[?&]' + name + '(=([^&#]*)|&|#|$)'),
        results = regex.exec(url);
    if (!results) return null;
    if (!results[2]) return '';
    return decodeURIComponent(results[2].replace(/\+/g, ' '));
}

let width = getParameterByName('w') || 180;
let height = getParameterByName('h') || 320;
let mode = getParameterByName('m') || 2;


let ctx = document.getElementsByClassName('sc-htpNat');
if (ctx.length > 0) {
	ctx = ctx[0].contentWindow; 
} else {
	ctx = window;
}

window.neyboyChallenge = new NeyboyChallenge(ctx, 'c2canvas', parseInt(width, 10), parseInt(height, 10), parseInt(mode, 10));

