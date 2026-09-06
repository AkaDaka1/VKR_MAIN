package com.vkr.theaterclient.ui.navigation

import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import com.vkr.theaterclient.ui.TheaterViewModel
import com.vkr.theaterclient.ui.screens.AuthScreen
import com.vkr.theaterclient.ui.screens.ReservationsScreen
import com.vkr.theaterclient.ui.screens.SeatsScreen
import com.vkr.theaterclient.ui.screens.ShowsScreen
import com.vkr.theaterclient.ui.screens.TheatersScreen

@Composable
fun TheaterNavHost() {
    val navController = rememberNavController()
    val viewModel: TheaterViewModel = hiltViewModel()
    LaunchedEffect(Unit) {
        viewModel.checkSession()
    }

    NavHost(navController = navController, startDestination = Routes.AUTH) {
        composable(Routes.AUTH) {
            AuthScreen(
                viewModel = viewModel,
                onAuthenticated = {
                    navController.navigate(Routes.THEATERS) {
                        popUpTo(Routes.AUTH) { inclusive = true }
                        launchSingleTop = true
                    }
                },
            )
        }
        composable(Routes.THEATERS) {
            TheatersScreen(
                viewModel = viewModel,
                onTheaterClick = { theaterId -> navController.navigate(Routes.shows(theaterId)) },
                onReservationsClick = { navController.navigate(Routes.RESERVATIONS) },
            )
        }
        composable(
            route = Routes.SHOWS,
            arguments = listOf(navArgument("theaterId") { type = NavType.IntType }),
        ) { backStack ->
            val theaterId = backStack.arguments?.getInt("theaterId") ?: return@composable
            ShowsScreen(
                theaterId = theaterId,
                viewModel = viewModel,
                onShowClick = { showId -> navController.navigate(Routes.seats(showId)) },
            )
        }
        composable(
            route = Routes.SEATS,
            arguments = listOf(navArgument("showId") { type = NavType.IntType }),
        ) { backStack ->
            val showId = backStack.arguments?.getInt("showId") ?: return@composable
            SeatsScreen(
                showId = showId,
                viewModel = viewModel,
            )
        }
        composable(Routes.RESERVATIONS) {
            ReservationsScreen(viewModel = viewModel)
        }
    }
}
