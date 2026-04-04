import { useEffect } from 'react';
import { track } from '../analytics';
import { staticUrl } from '../config';
import './关于.css';

function 关于() {
  useEffect(() => { track('Visit 关于 Page'); }, []);

  return (
    <div className="about">
      <div className="about-image">
        <img src={staticUrl('kungfuchess.jpg')} alt="项目原始版本" />
        <div className="about-image-caption">项目原始版本截图。</div>
      </div>
      <div className="about-text">
        <p>
          本项目当前版本以双人实时中国象棋为目标，强调同步走子、实时状态同步与回放能力。
          of games like StarCraft, Command &amp; Conquer, and Age of Empires to a classic setting. It was originally
          released in 2002 by Shizmoo Games and was popular through the mid-2000s. This is a reinvention of the game
          using modern technology and game design to bring out its potential. I hope you enjoy playing!
        </p>

        <p>
          If you have feedback, please stop by our{' '}
          <a href="https://www.reddit.com/r/kfchess/" target="_blank" rel="noopener noreferrer">reddit</a>, reach out to{' '}
          <a href="mailto:contact@real-time-chess-battle.example.com">contact@real-time-chess-battle.example.com</a>, or check out the {' '}
          <a href="https://github.com/paladin8/kfchess-cc" target="_blank" rel="noopener noreferrer">code on GitHub</a>.
        </p>
      </div>
    </div>
  );
}

export default 关于;
