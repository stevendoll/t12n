import Nav from '../components/Nav'
import Footer from '../components/Footer'
import VoiceBox from '../components/VoiceBox'

export default function Home() {
  return (
    <>
      <Nav />

      <section className="min-h-screen flex flex-col justify-center items-center px-12 py-[60px] pb-20 relative text-center">
        <img
          src="/assets/t12n-ai-rabbit.png"
          alt="t12n.ai rabbit logo"
          className="w-40 h-40 mb-8 opacity-0 animate-[fadeUp_0.8s_0.1s_forwards]"
        />
        <div className="text-[0.68rem] tracking-[0.2em] uppercase text-[var(--accent)] mb-8 opacity-0 animate-[fadeUp_0.8s_0.2s_forwards]">
          AI Transformation Consulting
        </div>
        <VoiceBox />
      </section>

      <hr className="w-full max-w-[1200px] mx-auto border-none border-t border-[var(--border)]" />

      <section className="max-w-[900px] mx-auto px-12 py-[120px] text-center" id="about">
        <div className="text-[0.68rem] tracking-[0.2em] uppercase text-[var(--accent)] mb-6">About</div>
        <h2 className="font-serif text-[clamp(2rem,4vw,3.5rem)] leading-[1.05] tracking-[-0.02em] mb-8">
          Built on urgency.<br /><em className="font-serif italic text-[rgba(245,240,232,0.4)]">Grounded in reality.</em>
        </h2>
        <div className="grid grid-cols-4 gap-[2px] mt-2 mb-12">
          {[
            { num: '12+', desc: 'Years in enterprise technology' },
            { num: '40+', desc: 'Organizations transformed' },
            { num: '$2B+', desc: 'In value unlocked' },
            { num: 'Day 1', desc: 'Mindset, always' },
          ].map(({ num, desc }) => (
            <div key={num} className="border border-[var(--border)] p-7 px-6 bg-[rgba(245,240,232,0.02)]">
              <div className="font-serif text-[2.8rem] text-[var(--accent)] leading-none mb-2">{num}</div>
              <div className="text-[0.68rem] tracking-[0.1em] uppercase text-[rgba(245,240,232,0.3)] leading-[1.5]">{desc}</div>
            </div>
          ))}
        </div>
        <div className="text-[0.88rem] leading-[1.85] text-[rgba(245,240,232,0.55)] space-y-5 text-left max-w-[680px] mx-auto">
          <p>I founded <strong className="text-[var(--white)] font-normal">AI Transformation (t12n.ai)</strong> because I kept seeing the same pattern: smart leaders at great companies, frozen. Not by lack of ambition — but by the gap between knowing AI matters and knowing what to actually do about it.</p>
          <p>My work sits at the intersection of <strong className="text-[var(--white)] font-normal">executive strategy, technical implementation, and organizational change</strong>. I don't just advise — I embed, build, and help you run.</p>
          <p>Before t12n, I led AI initiatives at Fortune 500 companies and venture-backed startups alike. I've seen what separates organizations that thrive in this moment from those that don't. It's almost never about the technology.</p>
          <p>It's about <strong className="text-[var(--white)] font-normal">speed of decision, clarity of ownership, and the courage to move before everything is certain</strong>. That's what I help you build.</p>
        </div>
      </section>

      <section className="max-w-[900px] mx-auto px-12 pb-[120px] text-center" id="services">
        <div className="text-[0.68rem] tracking-[0.2em] uppercase text-[var(--accent)] mb-[60px]">What I do</div>
        <div className="grid grid-cols-3 gap-[2px]">
          {[
            {
              num: '01',
              title: 'AI Strategy & Roadmapping',
              desc: 'From audit to action plan in 30 days. Where are you losing ground? Where can AI compound your advantage? We map it, prioritize it, and make it executable.',
            },
            {
              num: '02',
              title: 'Executive Alignment',
              desc: "The hardest part of AI transformation isn't the AI. I facilitate leadership alignment that turns cautious committees into decisive sponsors.",
            },
            {
              num: '03',
              title: 'Implementation Oversight',
              desc: 'I embed with your teams to ensure strategy becomes working systems. From vendor selection to go-live, with zero tolerance for vaporware.',
            },
          ].map(({ num, title, desc }) => (
            <div
              key={num}
              className="border border-[var(--border)] p-10 px-9 bg-[rgba(245,240,232,0.02)] relative overflow-hidden transition-colors group hover:bg-[rgba(77,182,172,0.04)] before:content-[''] before:absolute before:top-0 before:left-0 before:w-0 before:h-[2px] before:bg-[var(--accent)] before:transition-[width] before:duration-400 hover:before:w-full"
            >
              <div className="text-[0.65rem] tracking-[0.15em] text-[rgba(245,240,232,0.2)] mb-6">{num}</div>
              <div className="font-serif text-2xl leading-[1.1] mb-4">{title}</div>
              <div className="text-[0.8rem] leading-[1.8] text-[rgba(245,240,232,0.4)]">{desc}</div>
            </div>
          ))}
        </div>
      </section>

      <Footer />
    </>
  )
}
