import Nav from '../components/Nav'
import Footer from '../components/Footer'
import VoiceBox from '../components/VoiceBox'
import ContactForm from '../components/ContactForm'

export default function Home() {
  return (
    <>
      <Nav />

      <section id="hero">
        <img src="/assets/t12n-ai-rabbit.png" alt="t12n.ai rabbit logo" />
        <div className="label">AI Transformation</div>
        <h1 className="hero-headline">This is the biggest shift most of us will see in our working lives.</h1>
        <VoiceBox />
      </section>


      <section id="about">
        <div className="section-label">About</div>
        <h2>
          The org on the other side of this isn't just faster.<br />
          <em>It's one you're not embarrassed to have built.</em>
        </h2>
        <div className="stats-grid">
          {[
            { num: '12+', desc: 'Years doing this, not talking about doing this' },
            { num: '12+', desc: 'Processes actually transformed — not workshopped' },
            { num: '$16M+', desc: 'In value that showed up on a P&L, not a slide' },
            { num: 'Day 1', desc: 'Mindset, always' },
          ].map(({ num, desc }) => (
            <div key={desc} className="stat-cell">
              <div className="stat-num">{num}</div>
              <div className="stat-desc">{desc}</div>
            </div>
          ))}
        </div>
        <div className="about-body">
          <p>In five years, some organizations will look back at this moment as the one where everything got faster, clearer, better. Others will land in one of two failures: the ones who waited for certainty that never came, and the ones who moved so fast they built something they can't defend. Both end up behind — and unable to explain how they got there.</p>
          <p>Here's the part most people selling AI transformation won't say out loud: it's drinking your local reservoir to help someone draft an email, concentrating an enormous amount of power in about nine companies, making misinformation cheaper to produce than the truth, pricing some customers based on what an algorithm thinks they'll tolerate — and yes, somewhere right now, helping choose targets on an actual battlefield.</p>
          <p>None of that is exaggerated. None of it is a reason to sit this one out.</p>
          <p>The mistrust is earned. The paralysis isn't. <strong>These problems are real. They're also solvable</strong> — by people who refuse to choose between moving fast and doing right.</p>
        </div>
      </section>


      <section id="the-work">
        <div className="section-label">The Work</div>
        <h2>
          Not a roadmap deck.<br />
          <em>Not a vendor bake-off.</em>
        </h2>
        <div className="about-body">
          <p>Not three tiers of service with a discount if you buy the bundle. I embed with your team, we find the two or three moves that actually matter for you, and we make them — with the uncomfortable parts of this technology on the table the whole time, not swept under it.</p>
          <p><strong>You bring the problem that's actually keeping you up. I bring twelve years of doing this without the theater.</strong></p>
        </div>
      </section>


      <section id="contact">
        <div className="section-label">Contact</div>
        <h2 className="contact-heading">
          Let's talk about<br />
          <em>what's actually blocking you.</em>
        </h2>
        <ContactForm />
      </section>


      <Footer />
    </>
  )
}
