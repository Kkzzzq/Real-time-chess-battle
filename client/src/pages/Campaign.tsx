/**
 * Campaign Page
 * 第一版已冻结/下线，仅显示说明，不再发起任何 campaign API 请求。
 */

import { Link } from 'react-router-dom';
import './Campaign.css';

function Campaign() {
  return (
    <div className="campaign">
      <div className="campaign-header">
        <h1 className="campaign-title">战役模式已下线</h1>
        <p className="campaign-subtitle">
          第一版仅保留双人实时中国象棋主链路，战役模式暂时冻结，后续重构完成后再开放。
        </p>
      </div>

      <div className="campaign-error" role="status" aria-live="polite">
        当前版本不支持进入战役模式，也不再创建战役对局。
      </div>

      <div className="campaign-loading" style={{ marginTop: 24 }}>
        <Link to="/" style={{ color: 'inherit', textDecoration: 'underline' }}>
          返回首页
        </Link>
      </div>
    </div>
  );
}

export default Campaign;
