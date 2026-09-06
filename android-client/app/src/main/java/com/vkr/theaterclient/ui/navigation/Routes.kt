package com.vkr.theaterclient.ui.navigation

object Routes {
    const val AUTH = "auth"
    const val THEATERS = "theaters"
    const val SHOWS = "shows/{theaterId}"
    const val SEATS = "seats/{showId}"
    const val RESERVATIONS = "reservations"

    fun shows(theaterId: Int) = "shows/$theaterId"
    fun seats(showId: Int) = "seats/$showId"
}
