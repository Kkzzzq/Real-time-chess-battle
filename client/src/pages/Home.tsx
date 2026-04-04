import { useState, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useLobbyStore } from '../stores/lobby';
import { track } from '../analytics';
import { staticUrl } from '../config';
import './Home.css';

type BoardType = 'standard';
type Speed = 'standard' | 'lightning';

function Home() {
  const navigate = useNavigate();
  const createLobby = useLobbyStore((s) => s.createLobby);
  const connect = useLobbyStore((s) => s.connect);

  const [isCreating, setIsCreating] = useState(false);
  const [selectedBoardType, setSelectedBoardType] = useState<BoardType>('standard');
  const [showBoardTypeModal, setShowBoardTypeModal] = useState(false);
  const [showCreateLobbyModal, setShowCreateLobbyModal] = useState(false);
  const [isCreatingLobby, setIsCreatingLobby] = useState(false);
  const [addAiToLobby, setAddAiToLobby] = useState(false);
  const [speed, setSpeed] = useState<Speed>(() => {
    return (localStorage.getItem('friendlySpeed') as Speed) || 'standard';
  });

  useEffect(() => { track('Visit Home Page'); }, []);

  const handleSpeedChange = (newSpeed: Speed) => {
    setSpeed(newSpeed);
    localStorage.setItem('friendlySpeed', newSpeed);
    track('Change Friendly Speed', { speed: newSpeed });
  };

  const handlePlayVsAI = () => {
    setShowBoardTypeModal(true);
  };

  const handleStartGame = async () => {
    if (isCreating) return;
    setIsCreating(true);

    try {
      const playerCount = 2;
      const code = await createLobby(
        {
          isPublic: false,
          speed,
          playerCount,
          isRanked: false,
        },
        true
      );

      const state = useLobbyStore.getState();
      if (state.playerKey) {
        connect(code, state.playerKey);
      }
      navigate(`/lobby/${code}`);
      track('Create New Game', { speed, isBot: true, boardType: selectedBoardType, playerCount });
    } catch (error) {
      console.error('Failed to create game:', error);
      alert('Failed to create game. Please try again.');
    } finally {
      setIsCreating(false);
      setShowBoardTypeModal(false);
    }
  };

  const handlePlayVsFriend = async () => {
    if (isCreating) return;
    setIsCreating(true);

    try {
      const code = await createLobby(
        {
          isPublic: false,
          speed,
          playerCount: 2,
          isRanked: false,
        },
        false
      );

      const state = useLobbyStore.getState();
      if (state.playerKey) {
        connect(code, state.playerKey);
      }
      navigate(`/lobby/${code}`);
      track('Create New Game', { speed, isBot: false, playerCount: 2 });
    } catch (error) {
      console.error('Failed to create game:', error);
      alert('Failed to create game. Please try again.');
    } finally {
      setIsCreating(false);
    }
  };

  const handle战役 = () => {
    navigate('/campaign');
  };

  const handleCreateLobbySubmit = useCallback(async () => {
    if (isCreatingLobby) return;
    setIsCreatingLobby(true);

    try {
      const code = await createLobby(
        {
          isPublic: false,
          speed: 'standard',
          playerCount: 2,
          isRanked: false,
        },
        addAiToLobby
      );

      const state = useLobbyStore.getState();
      if (state.playerKey) {
        connect(code, state.playerKey);
      }
      navigate(`/lobby/${code}`);
    } catch (error) {
      console.error('Failed to create lobby:', error);
      alert('Failed to create lobby. Please try again.');
    } finally {
      setIsCreatingLobby(false);
      setShowCreateLobbyModal(false);
      setAddAiToLobby(false);
    }
  }, [createLobby, connect, navigate, addAiToLobby, isCreatingLobby]);

  return (
    <div className="home">
      <div className="home-banner">
        <div className="home-banner-inner">
          <div className="home-banner-video">
            <video autoPlay loop muted playsInline>
              <source src={staticUrl('banner-video.mp4')} type="video/mp4" />
            </video>
          </div>
          <div className="home-banner-text">
            <div className="home-banner-text-main">无回合制中国象棋</div>
            <div className="home-banner-text-sub">
              双人同步走子的实时中国象棋体验。
            </div>
          </div>
        </div>
      </div>

      <div className="home-play-buttons">
        <div className="home-play-button-wrapper">
          <button className="home-play-button" onClick={handle战役}>
            战役
          </button>
          <div className="home-play-subtitle">单人闯关</div>
        </div>

        <div className="home-play-button-wrapper">
          <button
            className="home-play-button"
            onClick={handlePlayVsAI}
            disabled={isCreating}
          >
            {isCreating ? '创建中...' : '与 AI 对弈'}
          </button>
          <div className="home-play-option-wrapper">
            <button
              className={`home-play-option ${speed === 'standard' ? 'selected' : ''}`}
              onClick={() => handleSpeedChange('standard')}
            >
              标准
            </button>
            <button
              className={`home-play-option ${speed === 'lightning' ? 'selected' : ''}`}
              onClick={() => handleSpeedChange('lightning')}
            >
              闪电
            </button>
          </div>
        </div>

        <div className="home-play-button-wrapper">
          <button
            className="home-play-button"
            onClick={handlePlayVsFriend}
            disabled={isCreating}
          >
            与好友对弈
          </button>
          <div className="home-play-option-wrapper">
            <button
              className={`home-play-option ${speed === 'standard' ? 'selected' : ''}`}
              onClick={() => handleSpeedChange('standard')}
            >
              标准
            </button>
            <button
              className={`home-play-option ${speed === 'lightning' ? 'selected' : ''}`}
              onClick={() => handleSpeedChange('lightning')}
            >
              闪电
            </button>
          </div>
        </div>
      </div>

      {/* Board Type Selection Modal */}
      {showBoardTypeModal && (
        <div className="modal-overlay" onClick={() => setShowBoardTypeModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>选择棋盘模式</h2>
            <div className="board-type-options">
              <label className={`board-type-option ${selectedBoardType === 'standard' ? 'selected' : ''}`}>
                <input
                  type="radio"
                  name="boardType"
                  value="standard"
                  checked={selectedBoardType === 'standard'}
                  onChange={() => setSelectedBoardType('standard')}
                />
                <div className="board-type-info">
                  <h3>标准棋盘（9×10）</h3>
                  <p>双人实时中国象棋棋盘</p>
                </div>
              </label>
                          </div>
            <div className="modal-actions">
              <button className="btn btn-secondary" onClick={() => setShowBoardTypeModal(false)}>
                取消
              </button>
              <button className="btn btn-primary" onClick={handleStartGame} disabled={isCreating}>
                {isCreating ? '创建中...' : '开始对局'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create Lobby Modal */}
      {showCreateLobbyModal && (
        <div className="modal-overlay" onClick={() => setShowCreateLobbyModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>创建房间</h2>
            <div className="board-type-options">
              <label className={`board-type-option ${!addAiToLobby ? 'selected' : ''}`}>
                <input
                  type="radio"
                  name="lobbyType"
                  checked={!addAiToLobby}
                  onChange={() => setAddAiToLobby(false)}
                />
                <div className="board-type-info">
                  <h3>等待玩家</h3>
                  <p>创建一个房间，等待其他玩家加入</p>
                </div>
              </label>
              <label className={`board-type-option ${addAiToLobby ? 'selected' : ''}`}>
                <input
                  type="radio"
                  name="lobbyType"
                  checked={addAiToLobby}
                  onChange={() => setAddAiToLobby(true)}
                />
                <div className="board-type-info">
                  <h3>与 AI 对弈</h3>
                  <p>创建一个带 AI 对手的房间</p>
                </div>
              </label>
            </div>
            <div className="modal-actions">
              <button className="btn btn-secondary" onClick={() => setShowCreateLobbyModal(false)}>
                取消
              </button>
              <button className="btn btn-primary" onClick={handleCreateLobbySubmit} disabled={isCreatingLobby}>
                {isCreatingLobby ? 'Creating...' : 'Create Lobby'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Home;
