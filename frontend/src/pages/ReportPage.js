import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Building2,
  TrendingUp,
  Globe,
  Package,
  Newspaper,
  ExternalLink,
  Users,
  DollarSign,
  Target,
  Zap,
  MapPin,
  Layers,
  BarChart2,
} from 'lucide-react';
import './ReportPage.css';

/* ─────────────────────────────── Tab definitions ────────────────────────── */
const TABS = [
  { id: 'overview',   label: 'Overview',    icon: Building2   },
  { id: 'financial',  label: 'Financial',   icon: TrendingUp  },
  { id: 'market',     label: 'Market',      icon: Globe       },
  { id: 'products',   label: 'Products',    icon: Package     },
  { id: 'news',       label: 'News & Sources', icon: Newspaper },
];

/* ─────────────────────────────── Small helpers ──────────────────────────── */
const Section = ({ icon: Icon, title, color, children }) => (
  <div className="rp-section">
    <div className={`rp-section-header rp-color-${color}`}>
      <Icon size={18} />
      <h3>{title}</h3>
    </div>
    <div className="rp-section-body">{children}</div>
  </div>
);

const Tag = ({ children }) => <span className="rp-tag">{children}</span>;

const BulletList = ({ items, emptyMsg = 'No data available.' }) =>
  items && items.length > 0 ? (
    <ul className="rp-bullet-list">
      {items.map((item, i) => <li key={i}>{item}</li>)}
    </ul>
  ) : <p className="rp-muted">{emptyMsg}</p>;

const KV = ({ label, value }) => value ? (
  <div className="rp-kv">
    <span className="rp-kv-label">{label}</span>
    <span className="rp-kv-value">{value}</span>
  </div>
) : null;

/* ─────────────────────────────── Tab panels ─────────────────────────────── */

const OverviewPanel = ({ data }) => (
  <div className="rp-panel">
    <Section icon={Building2} title="Company Overview" color="blue">
      {data.year_founded && (
        <KV label="Founded" value={data.year_founded} />
      )}
      <p className="rp-overview-text" style={data.year_founded ? {marginTop: '1rem'} : {}}>
        {data.overview || 'No overview available.'}
      </p>
    </Section>

    <Section icon={Users} title="Key Executives" color="purple">
      {data.key_executives && data.key_executives.length > 0 ? (
        <div className="rp-exec-grid">
          {data.key_executives.map((exec, i) => (
            <div key={i} className="rp-exec-card">
              <div className="rp-exec-avatar">
                {(exec.name || 'N').charAt(0).toUpperCase()}
              </div>
              <div>
                <strong className="rp-exec-name">{exec.name}</strong>
                <span className="rp-exec-role">{exec.role}</span>
              </div>
            </div>
          ))}
        </div>
      ) : <p className="rp-muted">No executives found.</p>}
    </Section>
  </div>
);

const FinancialPanel = ({ fin, deep }) => {
  if (!fin && !deep) return <div className="rp-panel"><p className="rp-muted">Financial analysis not available.</p></div>;
  return (
    <div className="rp-panel">
      {/* ── Surface-level summary ── */}
      {fin && (
        <>
          <Section icon={DollarSign} title="Revenue & Valuation" color="green">
            <KV label="Revenue"              value={fin.revenue} />
            <KV label="Valuation"            value={fin.valuation} />
            <KV label="Profitability"        value={fin.profitability} />
            <KV label="Years to profitable" value={fin.years_to_profitability} />
          </Section>

          <Section icon={BarChart2} title="Funding Rounds" color="teal">
            <BulletList items={fin.funding_rounds} emptyMsg="No funding data found." />
          </Section>

          <Section icon={Zap} title="Key Financial Metrics" color="yellow">
            {fin.key_financial_metrics && fin.key_financial_metrics.length > 0 ? (
              <div className="rp-tag-group">
                {fin.key_financial_metrics.map((m, i) => <Tag key={i}>{m}</Tag>)}
              </div>
            ) : <p className="rp-muted">No additional metrics available.</p>}
          </Section>
        </>
      )}

      {/* ── Deep-dive sections ── */}
      {deep && (
        <>
          {/* Revenue over time table */}
          {deep.revenue_over_time && deep.revenue_over_time.length > 0 && (
            <Section icon={TrendingUp} title="Revenue Over Time" color="green">
              <table className="rp-table">
                <thead>
                  <tr><th>Year</th><th>Revenue</th><th>YoY Growth</th></tr>
                </thead>
                <tbody>
                  {deep.revenue_over_time.map((r, i) => (
                    <tr key={i}>
                      <td>{r.year}</td>
                      <td>{r.revenue}</td>
                      <td>{r.growth || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Section>
          )}

          {/* Investor profiles */}
          {deep.key_investors && deep.key_investors.length > 0 && (
            <Section icon={Users} title="Key Investors" color="purple">
              <div className="rp-investor-list">
                {deep.key_investors.map((inv, i) => (
                  <div key={i} className="rp-investor-card">
                    <div className="rp-investor-header">
                      <span className="rp-investor-name">{inv.name}</span>
                      {inv.type && <span className="rp-tag">{inv.type}</span>}
                    </div>
                    {inv.reason_for_investing && (
                      <p className="rp-investor-reason">"{inv.reason_for_investing}"</p>
                    )}
                    {inv.notable_portfolio && inv.notable_portfolio.length > 0 && (
                      <div className="rp-tag-group" style={{marginTop:'0.5rem'}}>
                        {inv.notable_portfolio.map((p, j) => (
                          <span key={j} className="rp-tag rp-tag--dim">{p}</span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </Section>
          )}

          {/* Investment thesis */}
          {deep.investment_thesis && (
            <Section icon={Zap} title="Investment Thesis" color="blue">
              <p style={{margin:0}}>{deep.investment_thesis}</p>
            </Section>
          )}

          {/* Capital deployment */}
          {deep.capital_deployment && deep.capital_deployment.length > 0 && (
            <Section icon={BarChart2} title="How Capital Was Deployed" color="teal">
              <BulletList items={deep.capital_deployment} />
            </Section>
          )}

          {/* Expense strategy */}
          {deep.expense_strategy && (
            <Section icon={DollarSign} title="Expense Strategy" color="yellow">
              <p style={{margin:0}}>{deep.expense_strategy}</p>
            </Section>
          )}

          {/* Future outlook */}
          {deep.future_outlook && (
            <Section icon={Globe} title="Future Outlook" color="orange">
              <p style={{margin:0}}>{deep.future_outlook}</p>
            </Section>
          )}

          {/* Key risks */}
          {deep.key_risks && deep.key_risks.length > 0 && (
            <Section icon={Target} title="Key Risks" color="red">
              <BulletList items={deep.key_risks} />
            </Section>
          )}

          {/* Deep sources */}
          {deep.sources && deep.sources.length > 0 && (
            <Section icon={ExternalLink} title="Sources" color="gray">
              <ul className="rp-source-list">
                {[...(fin?.sources || []), ...deep.sources]
                  .filter((s, i, a) => a.indexOf(s) === i)
                  .map((s, i) => (
                    <li key={i}><a href={s} target="_blank" rel="noopener noreferrer">
                      {s.length > 70 ? s.slice(0, 70) + '…' : s}
                    </a></li>
                  ))}
              </ul>
            </Section>
          )}
        </>
      )}

      {/* Fallback sources if no deep */}
      {!deep && fin?.sources && fin.sources.length > 0 && (
        <Section icon={ExternalLink} title="Financial Sources" color="gray">
          <ul className="rp-source-list">
            {fin.sources.map((s, i) => (
              <li key={i}><a href={s} target="_blank" rel="noopener noreferrer">
                {s.length > 70 ? s.slice(0, 70) + '…' : s}
              </a></li>
            ))}
          </ul>
        </Section>
      )}
    </div>
  );
};

const MarketPanel = ({ market }) => {
  if (!market) return <div className="rp-panel"><p className="rp-muted">Market analysis not available.</p></div>;
  return (
    <div className="rp-panel">
      <Section icon={Layers} title="Market Segment & Customers" color="blue">
        <KV label="Market segment"    value={market.market_segment} />
        <KV label="Target customers"  value={market.target_customers} />
      </Section>

      <Section icon={MapPin} title="Geographic Presence" color="teal">
        {market.geographic_presence && market.geographic_presence.length > 0 ? (
          <div className="rp-tag-group">
            {market.geographic_presence.map((g, i) => <Tag key={i}>{g}</Tag>)}
          </div>
        ) : <p className="rp-muted">No geographic data available.</p>}
      </Section>

      <Section icon={Zap} title="Competitive Advantages" color="purple">
        <BulletList items={market.competitive_advantages} emptyMsg="No advantages listed." />
      </Section>

      <Section icon={Target} title="Competitors" color="red">
        {market.competitors && market.competitors.length > 0 ? (
          <div className="rp-tag-group">
            {market.competitors.map((c, i) => <Tag key={i}>{c}</Tag>)}
          </div>
        ) : <p className="rp-muted">No competitors identified.</p>}
      </Section>

      <Section icon={Globe} title="Recent Strategic Moves" color="orange">
        <BulletList items={market.recent_strategic_moves} emptyMsg="No strategic moves found." />
      </Section>

      {market.sources && market.sources.length > 0 && (
        <Section icon={ExternalLink} title="Market Sources" color="gray">
          <ul className="rp-source-list">
            {market.sources.map((s, i) => (
              <li key={i}><a href={s} target="_blank" rel="noopener noreferrer">{s.length > 70 ? s.slice(0, 70) + '…' : s}</a></li>
            ))}
          </ul>
        </Section>
      )}
    </div>
  );
};

const ProductsPanel = ({ product }) => {
  if (!product) return <div className="rp-panel"><p className="rp-muted">Product analysis not available.</p></div>;
  return (
    <div className="rp-panel">
      <Section icon={Package} title="Core Products & Services" color="blue">
        {product.core_products && product.core_products.length > 0 ? (
          <div className="rp-tag-group">
            {product.core_products.map((p, i) => <Tag key={i}>{p}</Tag>)}
          </div>
        ) : <p className="rp-muted">No products listed.</p>}
      </Section>

      <Section icon={Layers} title="Technology Stack" color="teal">
        {product.technology_stack && product.technology_stack.length > 0 ? (
          <div className="rp-tag-group">
            {product.technology_stack.map((t, i) => <Tag key={i}>{t}</Tag>)}
          </div>
        ) : <p className="rp-muted">Technology stack not available.</p>}
      </Section>

      <Section icon={Zap} title="Product Highlights" color="purple">
        <BulletList items={product.product_highlights} emptyMsg="No highlights found." />
      </Section>

      <Section icon={DollarSign} title="Pricing Model" color="green">
        <p>{product.pricing_model || 'Pricing model not publicly available.'}</p>
      </Section>

      {product.sources && product.sources.length > 0 && (
        <Section icon={ExternalLink} title="Product Sources" color="gray">
          <ul className="rp-source-list">
            {product.sources.map((s, i) => (
              <li key={i}><a href={s} target="_blank" rel="noopener noreferrer">{s.length > 70 ? s.slice(0, 70) + '…' : s}</a></li>
            ))}
          </ul>
        </Section>
      )}
    </div>
  );
};

const NewsPanel = ({ data }) => (
  <div className="rp-panel">
    <Section icon={Newspaper} title="Recent News & Milestones" color="orange">
      <BulletList items={data.recent_news} emptyMsg="No recent news available." />
    </Section>

    <Section icon={ExternalLink} title="All Sources" color="gray">
      {data.sources && data.sources.length > 0 ? (
        <ul className="rp-source-list">
          {data.sources.map((s, i) => (
            <li key={i}>
              <a href={s} target="_blank" rel="noopener noreferrer">
                <ExternalLink size={12} />
                {s.length > 80 ? s.slice(0, 80) + '…' : s}
              </a>
            </li>
          ))}
        </ul>
      ) : <p className="rp-muted">No sources provided.</p>}
    </Section>
  </div>
);

/* ─────────────────────────────── Main component ─────────────────────────── */
const ReportPage = ({ reportData }) => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    if (!reportData) navigate('/');
  }, [reportData, navigate]);

  if (!reportData) return null;

  const renderPanel = () => {
    switch (activeTab) {
      case 'overview':  return <OverviewPanel  data={reportData} />;
      case 'financial': return <FinancialPanel fin={reportData.financial_analysis} deep={reportData.financial_deep_analysis} />;
      case 'market':    return <MarketPanel    market={reportData.market_positioning} />;
      case 'products':  return <ProductsPanel  product={reportData.product_analysis} />;
      case 'news':      return <NewsPanel      data={reportData} />;
      default:          return null;
    }
  };

  return (
    <div className="report-page">
      {/* Back button */}
      <button className="back-btn" onClick={() => navigate('/')}>
        <ArrowLeft size={16} /> Back to Search
      </button>

      {/* Header */}
      <div className="report-header">
        <div className="report-header-text">
          <h2>{reportData.company_name}</h2>
          <span className="badge">Intelligence Report</span>
        </div>
      </div>

      {/* Tab bar */}
      <div className="rp-tab-bar">
        {TABS.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            className={`rp-tab ${activeTab === id ? 'rp-tab--active' : ''}`}
            onClick={() => setActiveTab(id)}
          >
            <Icon size={15} />
            <span>{label}</span>
          </button>
        ))}
      </div>

      {/* Active panel */}
      <div className="rp-tab-content">
        {renderPanel()}
      </div>
    </div>
  );
};

export default ReportPage;
