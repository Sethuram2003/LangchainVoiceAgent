import './PhoneFrame.css'

/** PhoneFrame — iOS-style device bezel wrapping the app. */
export function PhoneFrame({ children }) {
  return (
    <div className="phone-wrapper">
      <div className="phone-bezel">
        <div className="phone-screen">
          <div className="notch"><div className="notch-cam" /></div>
          <div className="phone-inner">{children}</div>
          <div className="home-bar" />
        </div>
      </div>
    </div>
  )
}