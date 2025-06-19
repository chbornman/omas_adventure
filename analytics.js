// PostHog Analytics Integration for Oma's Adventure
// This file should be included in the HTML page

// Initialize PostHog
!function(t,e){var o,n,p,r;e.__SV||(window.posthog=e,e._i=[],e.init=function(i,s,a){function g(t,e){var o=e.split(".");2==o.length&&(t=t[o[0]],e=o[1]);t[e]=function(){t.push([e].concat(Array.prototype.slice.call(arguments,0)))}}(p=t.createElement("script")).type="text/javascript",p.async=!0,p.src=s.api_host+"/static/array.js",(r=t.getElementsByTagName("script")[0]).parentNode.insertBefore(p,r);var u=e;for(void 0!==a?u=e[a]=[]:a="posthog",u.people=u.people||[],u.toString=function(t){var e="posthog";return"posthog"!==a&&(e+="."+a),t||(e+=" (stub)"),e},u.people.toString=function(){return u.toString(1)+".people (stub)"},o="capture identify alias people.set people.set_once set_config register register_once unregister opt_out_capturing has_opted_out_capturing opt_in_capturing reset isFeatureEnabled onFeatureFlags getFeatureFlag getFeatureFlagPayload reloadFeatureFlags group updateEarlyAccessFeatureEnrollment getEarlyAccessFeatures getActiveMatchingSurveys getSurveys onSessionId".split(" "),n=0;n<o.length;n++)g(u,o[n]);e._i.push([i,s,a])},e.__SV=1)}(document,window.posthog||[]);

// Initialize with your project token
posthog.init('phc_mH9LneDpqu1rcdC5mlN6Hmp5QwDq2uAgYW5YeIav5MX', {
    api_host: 'https://app.posthog.com'
});

// Global function to track events from Python
window.trackEvent = function(eventName, propertiesJson) {
    try {
        const properties = JSON.parse(propertiesJson);
        posthog.capture(eventName, properties);
        console.log('Tracked event:', eventName, properties);
    } catch (error) {
        console.error('Failed to track event:', error);
    }
};

// Track page load
posthog.capture('game_page_loaded', {
    timestamp: new Date().toISOString(),
    user_agent: navigator.userAgent,
    screen_resolution: `${screen.width}x${screen.height}`
});

console.log('PostHog analytics initialized');